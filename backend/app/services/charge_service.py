from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any
from app.core.config import settings


class ChargeService:
    """Deterministic Indian Market Charges and Slippage Engine.
    
    Models realistic transaction charges based on Indian brokerage structures:
    - Brokerage: 0.03% or flat ₹20 per executed order (whichever is lower for discount brokers)
    - STT (Securities Transaction Tax): 0.1% on delivery Buy & Sell
    - Exchange Turnover Charges: 0.00345% (NSE rate)
    - GST: 18% on (Brokerage + Exchange Turnover)
    - SEBI Turnover Charges: 0.0001% (₹10 per crore)
    - Stamp Duty: 0.015% on Buy delivery
    - Slippage: Configurable basis points applied to execution price
    """

    @classmethod
    def calculate_charges(
        cls,
        symbol: str,
        side: str,
        price: Decimal,
        quantity: int,
        order_type: str = "MARKET"
    ) -> Dict[str, Decimal]:
        if not settings.PAPER_CHARGES_ENABLED:
            return {
                "brokerage": Decimal("0.00"),
                "stt": Decimal("0.00"),
                "exchange_turnover": Decimal("0.00"),
                "gst": Decimal("0.00"),
                "sebi_charges": Decimal("0.00"),
                "stamp_duty": Decimal("0.00"),
                "total_charges": Decimal("0.00"),
            }

        turnover = price * Decimal(str(quantity))
        
        # 1. Brokerage
        if settings.PAPER_BROKERAGE_ENABLED:
            raw_brokerage = turnover * Decimal("0.0003")
            brokerage = min(raw_brokerage, Decimal("20.00"))
        else:
            brokerage = Decimal("0.00")

        # 2. STT / CTT (0.1% on turnover)
        stt = turnover * Decimal("0.001")

        # 3. Exchange transaction fee (0.00345%)
        exchange_turnover = turnover * Decimal("0.0000345")

        # 4. GST (18% on Brokerage + Exchange Turnover)
        gst = (brokerage + exchange_turnover) * Decimal("0.18")

        # 5. SEBI turnover fee (₹10 per crore = 0.000001)
        sebi_charges = turnover * Decimal("0.000001")

        # 6. Stamp duty (0.015% on BUY only)
        stamp_duty = (turnover * Decimal("0.00015")) if side.upper() == "BUY" else Decimal("0.00")

        total = brokerage + stt + exchange_turnover + gst + sebi_charges + stamp_duty

        def d_round(val: Decimal) -> Decimal:
            return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "turnover": d_round(turnover),
            "brokerage": d_round(brokerage),
            "stt": d_round(stt),
            "exchange_turnover": d_round(exchange_turnover),
            "gst": d_round(gst),
            "sebi_charges": d_round(sebi_charges),
            "stamp_duty": d_round(stamp_duty),
            "total_charges": d_round(total),
        }

    @classmethod
    def apply_slippage(cls, base_price: Decimal, side: str, order_type: str = "MARKET") -> Decimal:
        """Applies configurable slippage (basis points) for simulated market orders."""
        if order_type.upper() != "MARKET" or settings.PAPER_SLIPPAGE_BPS <= 0:
            return base_price

        # 1 basis point = 0.01% = 0.0001
        bps_factor = Decimal(str(settings.PAPER_SLIPPAGE_BPS)) * Decimal("0.0001")
        if side.upper() == "BUY":
            # Buyer pays slightly higher in market order
            slipped = base_price * (Decimal("1.0") + bps_factor)
        else:
            # Seller gets slightly lower in market order
            slipped = base_price * (Decimal("1.0") - bps_factor)

        # Quantize to standard Indian tick size (0.05)
        tick = Decimal("0.05")
        rounded = (slipped / tick).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * tick
        return rounded.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
