import hmac
import hashlib
import uuid
import pytest
from decimal import Decimal
from sqlalchemy import select

from app.models.payment import PaymentOrder
from app.models.wallet import Wallet, LedgerEntry
from app.payments.razorpay_provider import RazorpayProvider
from app.payments.service import PaymentService


@pytest.mark.asyncio
async def test_razorpay_order_creation_and_history(client):
    # 1. Register & Login
    email = f"pay_user_{uuid.uuid4().hex[:6]}@nse.com"
    await client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": "Razorpay Tester"})
    login_res = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Invalid Amount (<= 0)
    invalid_res = await client.post("/api/v1/payments/create-order", json={"amount": -50.0}, headers=headers)
    assert invalid_res.status_code == 422 or invalid_res.status_code == 400

    # 3. Create Valid Payment Order (₹5,000)
    create_res = await client.post("/api/v1/payments/create-order", json={"amount": 5000.0, "currency": "INR"}, headers=headers)
    assert create_res.status_code == 201
    order_data = create_res.json()
    assert "razorpay_order_id" in order_data
    assert float(order_data["amount"]) == 5000.0
    assert order_data["status"] == "CREATED"
    assert "razorpay_key_id" in order_data
    order_id = order_data["razorpay_order_id"]

    # 4. Check Payment History contains the new order
    hist_res = await client.get("/api/v1/payments", headers=headers)
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert len(hist) >= 1
    assert hist[0]["razorpay_order_id"] == order_id


@pytest.mark.asyncio
async def test_razorpay_signature_verification_and_wallet_credit(client):
    email = f"verify_user_{uuid.uuid4().hex[:6]}@nse.com"
    await client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": "Verify Tester"})
    login_res = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Initial balance check
    wallet_res = await client.get("/api/v1/wallet", headers=headers)
    initial_balance = float(wallet_res.json()["available_balance"])

    # Create Order
    create_res = await client.post("/api/v1/payments/create-order", json={"amount": 10000.0}, headers=headers)
    assert create_res.status_code == 201
    rzp_order_id = create_res.json()["razorpay_order_id"]
    rzp_payment_id = f"pay_{uuid.uuid4().hex[:14]}"

    # 1. Invalid Signature Attempt
    invalid_verify_res = await client.post(
        "/api/v1/payments/verify",
        json={
            "razorpay_order_id": rzp_order_id,
            "razorpay_payment_id": rzp_payment_id,
            "razorpay_signature": "invalid_bogus_signature",
        },
        headers=headers,
    )
    assert invalid_verify_res.status_code == 400

    # 2. Valid Signature Attempt (in test simulation mode, test_sig_ prefix or valid hmac is verified)
    secret = "mock_secret_placeholder"
    msg = f"{rzp_order_id}|{rzp_payment_id}".encode("utf-8")
    valid_sig = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()

    valid_verify_res = await client.post(
        "/api/v1/payments/verify",
        json={
            "razorpay_order_id": rzp_order_id,
            "razorpay_payment_id": rzp_payment_id,
            "razorpay_signature": valid_sig,
        },
        headers=headers,
    )
    assert valid_verify_res.status_code == 200
    verify_data = valid_verify_res.json()
    assert verify_data["success"] is True
    assert verify_data["status"] == "PAID"
    assert float(verify_data["credited_amount"]) == 10000.0
    expected_new_balance = initial_balance + 10000.0
    assert float(verify_data["new_balance"]) == pytest.approx(expected_new_balance, 0.01)

    # 3. Check Wallet Available Balance updated
    wallet_after_res = await client.get("/api/v1/wallet", headers=headers)
    assert float(wallet_after_res.json()["available_balance"]) == pytest.approx(expected_new_balance, 0.01)

    # 4. Idempotency Check: Verify again with the exact same order
    repeat_verify_res = await client.post(
        "/api/v1/payments/verify",
        json={
            "razorpay_order_id": rzp_order_id,
            "razorpay_payment_id": rzp_payment_id,
            "razorpay_signature": valid_sig,
        },
        headers=headers,
    )
    assert repeat_verify_res.status_code == 200
    repeat_data = repeat_verify_res.json()
    assert repeat_data["success"] is True
    # Balance must NOT be doubled
    assert float(repeat_data["new_balance"]) == pytest.approx(expected_new_balance, 0.01)

    # Re-check wallet balance has NOT changed on duplicate submission
    wallet_repeat_res = await client.get("/api/v1/wallet", headers=headers)
    assert float(wallet_repeat_res.json()["available_balance"]) == pytest.approx(expected_new_balance, 0.01)


@pytest.mark.asyncio
async def test_razorpay_webhook_verification():
    """Test webhook signature validation and payload handling."""
    provider = RazorpayProvider(webhook_secret="test_secret_12345")
    payload = b'{"event":"payment.captured","payload":{"payment":{"entity":{"id":"pay_test123","order_id":"order_test123"}}}}'
    signature = hmac.new(b"test_secret_12345", payload, hashlib.sha256).hexdigest()

    assert provider.verify_webhook_signature(payload, signature) is True
    assert provider.verify_webhook_signature(payload, "invalid_sig") is False
