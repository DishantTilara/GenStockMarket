"""phase3_risk_engine

Revision ID: d4e2f8a1b345
Revises: c3b1e7f9a123
Create Date: 2026-10-01 21:13:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd4e2f8a1b345'
down_revision: Union[str, None] = 'c3b1e7f9a123'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. risk_settings table
    op.create_table(
        'risk_settings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('max_order_value', sa.Numeric(precision=20, scale=2), server_default='500000.00', nullable=False),
        sa.Column('max_daily_loss', sa.Numeric(precision=20, scale=2), server_default='25000.00', nullable=False),
        sa.Column('max_portfolio_exposure_pct', sa.Numeric(precision=5, scale=2), server_default='0.25', nullable=False),
        sa.Column('max_symbol_exposure_pct', sa.Numeric(precision=5, scale=2), server_default='0.10', nullable=False),
        sa.Column('max_position_value', sa.Numeric(precision=20, scale=2), server_default='200000.00', nullable=False),
        sa.Column('max_open_positions', sa.Integer(), server_default='10', nullable=False),
        sa.Column('max_quantity', sa.Integer(), server_default='500', nullable=False),
        sa.Column('max_daily_orders', sa.Integer(), server_default='50', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('idx_risk_settings_user', 'risk_settings', ['user_id'], unique=True)

    # 2. kill_switches table
    op.create_table(
        'kill_switches',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('scope', sa.String(length=30), server_default='PLATFORM', nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deactivated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_kill_switches_scope_user', 'kill_switches', ['scope', 'user_id'], unique=False)

    # 3. risk_events table
    op.create_table(
        'risk_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('side', sa.String(length=10), nullable=False),
        sa.Column('check_name', sa.String(length=50), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('severity', sa.String(length=20), server_default='INFO', nullable=False),
        sa.Column('rejection_code', sa.String(length=50), nullable=True),
        sa.Column('rejection_reason', sa.String(length=255), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_risk_events_user_time', 'risk_events', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_risk_events_user_time', table_name='risk_events')
    op.drop_table('risk_events')
    op.drop_index('idx_kill_switches_scope_user', table_name='kill_switches')
    op.drop_table('kill_switches')
    op.drop_index('idx_risk_settings_user', table_name='risk_settings')
    op.drop_table('risk_settings')
