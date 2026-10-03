"""phase2_aggregated_candles

Revision ID: c3b1e7f9a123
Revises: bf92ef0ade7a
Create Date: 2026-10-01 21:08:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3b1e7f9a123'
down_revision: Union[str, None] = 'bf92ef0ade7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'aggregated_candles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('instrument_id', sa.UUID(), nullable=True),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('exchange', sa.String(length=20), server_default='NSE', nullable=False),
        sa.Column('timeframe', sa.String(length=10), nullable=False),
        sa.Column('interval_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('open', sa.Numeric(precision=20, scale=4), nullable=False),
        sa.Column('high', sa.Numeric(precision=20, scale=4), nullable=False),
        sa.Column('low', sa.Numeric(precision=20, scale=4), nullable=False),
        sa.Column('close', sa.Numeric(precision=20, scale=4), nullable=False),
        sa.Column('volume', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('source', sa.String(length=32), server_default='market_provider', nullable=False),
        sa.Column('quality', sa.String(length=16), server_default='HIGH', nullable=False),
        sa.Column('is_complete', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['instrument_id'], ['instruments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'timeframe', 'interval_start', name='uq_symbol_timeframe_interval')
    )
    op.create_index('idx_candles_sym_tf_interval', 'aggregated_candles', ['symbol', 'timeframe', 'interval_start'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_candles_sym_tf_interval', table_name='aggregated_candles')
    op.drop_table('aggregated_candles')
