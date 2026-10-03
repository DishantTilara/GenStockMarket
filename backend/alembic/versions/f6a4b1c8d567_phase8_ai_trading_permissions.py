"""phase8_ai_trading_permissions

Revision ID: f6a4b1c8d567
Revises: e5f3a9b2c456
Create Date: 2026-10-01 21:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f6a4b1c8d567'
down_revision: Union[str, None] = 'e5f3a9b2c456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_trading_permissions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('auto_trading_enabled', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('auto_buy_enabled', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('auto_sell_enabled', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('require_risk_approval', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('max_order_value', sa.Numeric(precision=20, scale=2), server_default='50000.00', nullable=False),
        sa.Column('max_daily_loss', sa.Numeric(precision=20, scale=2), server_default='15000.00', nullable=False),
        sa.Column('max_position_value', sa.Numeric(precision=20, scale=2), server_default='100000.00', nullable=False),
        sa.Column('max_open_positions', sa.Integer(), server_default='5', nullable=False),
        sa.Column('max_daily_orders', sa.Integer(), server_default='20', nullable=False),
        sa.Column('allowed_symbols', sa.JSON(), nullable=False),
        sa.Column('allowed_exchanges', sa.JSON(), nullable=False),
        sa.Column('allowed_order_types', sa.JSON(), nullable=False),
        sa.Column('start_time', sa.String(length=10), server_default='09:15', nullable=False),
        sa.Column('end_time', sa.String(length=10), server_default='15:15', nullable=False),
        sa.Column('kill_switch_enabled', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('idx_ai_trading_perm_user', 'ai_trading_permissions', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_table('ai_trading_permissions')
