import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class AITradingPermission(Base):
    __tablename__ = "ai_trading_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Master switches (All default to False for safety)
    auto_trading_enabled = Column(Boolean, default=False, nullable=False)
    auto_buy_enabled = Column(Boolean, default=False, nullable=False)
    auto_sell_enabled = Column(Boolean, default=False, nullable=False)

    require_risk_approval = Column(Boolean, default=True, nullable=False)

    # Risk limits for AI execution
    max_order_value = Column(Numeric(20, 2), default=Decimal("50000.00"), nullable=False)
    max_daily_loss = Column(Numeric(20, 2), default=Decimal("15000.00"), nullable=False)
    max_position_value = Column(Numeric(20, 2), default=Decimal("100000.00"), nullable=False)
    max_open_positions = Column(Integer, default=5, nullable=False)
    max_daily_orders = Column(Integer, default=20, nullable=False)

    # Allowed filters
    allowed_symbols = Column(JSON, default=lambda: ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"], nullable=False)
    allowed_exchanges = Column(JSON, default=lambda: ["NSE"], nullable=False)
    allowed_order_types = Column(JSON, default=lambda: ["LIMIT", "MARKET"], nullable=False)

    # Trading window (IST format "09:15", "15:15")
    start_time = Column(String(10), default="09:15", nullable=False)
    end_time = Column(String(10), default="15:15", nullable=False)

    kill_switch_enabled = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", backref="ai_trading_permission")
