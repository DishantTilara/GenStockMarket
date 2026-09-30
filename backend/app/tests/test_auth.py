import pytest


@pytest.mark.asyncio
async def test_register_and_login_flow(client):
    # 1. Register
    reg_payload = {
        "email": "trader@dalalstreet.com",
        "password": "SecurePassword123!",
        "full_name": "Rakesh Jhunjhunwala"
    }
    res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "trader@dalalstreet.com"
    assert data["role"] == "trader"

    # 2. Login
    login_payload = {
        "email": "trader@dalalstreet.com",
        "password": "SecurePassword123!"
    }
    res = await client.post("/api/v1/auth/login", json=login_payload)
    assert res.status_code == 200
    token_data = res.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data

    # 3. Check me endpoint
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "trader@dalalstreet.com"
