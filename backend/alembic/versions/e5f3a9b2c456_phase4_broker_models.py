"""phase4_broker_models

Revision ID: e5f3a9b2c456
Revises: d4e2f8a1b345
Create Date: 2026-10-01 21:42:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e5f3a9b2c456'
down_revision: Union[str, None] = 'd4e2f8a1b345'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. broker_accounts
    op.create_table(
        'broker_accounts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('broker_name', sa.String(length=50), server_default='sandbox', nullable=False),
        sa.Column('environment', sa.String(length=20), server_default='SANDBOX', nullable=False),
        sa.Column('client_id', sa.String(length=100), nullable=True),
        sa.Column('api_key', sa.String(length=255), nullable=True),
        sa.Column('encrypted_secret', sa.String(length=500), nullable=True),
        sa.Column('encrypted_access_token', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_connected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_broker_accounts_user', 'broker_accounts', ['user_id'])

    # 2. broker_orders
    op.create_table(
        'broker_orders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('broker_account_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('broker_order_id', sa.String(length=100), nullable=False),
        sa.Column('internal_order_id', sa.UUID(), nullable=True),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('exchange', sa.String(length=20), server_default='NSE', nullable=False),
        sa.Column('side', sa.String(length=10), nullable=False),
        sa.Column('order_type', sa.String(length=20), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('status', sa.String(length=30), server_default='OPEN', nullable=False),
        sa.Column('filled_quantity', sa.Integer(), server_default='0', nullable=False),
        sa.Column('average_price', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('error_message', sa.String(length=500), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['broker_account_id'], ['broker_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_broker_orders_broker_id', 'broker_orders', ['broker_order_id'])
    op.create_index('idx_broker_orders_internal_id', 'broker_orders', ['internal_order_id'])

    # 3. broker_trades
    op.create_table(
        'broker_trades',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('broker_account_id', sa.UUID(), nullable=False),
        sa.Column('broker_trade_id', sa.String(length=100), nullable=False),
        sa.Column('broker_order_id', sa.String(length=100), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('side', sa.String(length=10), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price', sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['broker_account_id'], ['broker_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. broker_positions
    op.create_table(
        'broker_positions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('broker_account_id', sa.UUID(), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Integer(), server_default='0', nullable=False),
        sa.Column('buy_price', sa.Numeric(precision=20, scale=2), server_default='0.00', nullable=False),
        sa.Column('current_price', sa.Numeric(precision=20, scale=2), server_default='0.00', nullable=False),
        sa.Column('pnl', sa.Numeric(precision=20, scale=2), server_default='0.00', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['broker_account_id'], ['broker_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. broker_reconciliation_events
    op.create_table(
        'broker_reconciliation_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('broker_account_id', sa.UUID(), nullable=False),
        sa.Column('discrepancy_type', sa.String(length=100), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('resolved', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('resolution_notes', sa.String(length=500), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['broker_account_id'], ['broker_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('broker_reconciliation_events')
    op.drop_table('broker_positions')
    op.drop_table('broker_trades')
    op.drop_table('broker_orders')
    op.drop_table('broker_accounts')
