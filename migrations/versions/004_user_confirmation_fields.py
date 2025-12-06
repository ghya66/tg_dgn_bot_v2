"""
添加用户确认相关字段

为 energy_orders、orders、premium_orders 表添加：
- user_tx_hash: 用户确认的交易哈希
- user_confirmed_at: 用户确认时间
- user_confirm_source: 确认来源（仅 orders 表）
- fail_reason: 发货失败原因（仅 premium_orders 表）
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '004_user_confirmation_fields'
down_revision = '003_user_bindings'
branch_labels = None
depends_on = None


def upgrade():
    """添加用户确认相关字段"""
    # energy_orders 表
    op.add_column('energy_orders',
        sa.Column('user_tx_hash', sa.String(100), nullable=True))
    op.add_column('energy_orders',
        sa.Column('user_confirmed_at', sa.DateTime(), nullable=True))
    
    # orders 表
    op.add_column('orders',
        sa.Column('user_tx_hash', sa.String(100), nullable=True))
    op.add_column('orders',
        sa.Column('user_confirmed_at', sa.DateTime(), nullable=True))
    op.add_column('orders',
        sa.Column('user_confirm_source', sa.String(32), nullable=True))
    
    # premium_orders 表
    op.add_column('premium_orders',
        sa.Column('fail_reason', sa.String(500), nullable=True))


def downgrade():
    """回滚迁移"""
    # premium_orders 表
    op.drop_column('premium_orders', 'fail_reason')
    
    # orders 表
    op.drop_column('orders', 'user_confirm_source')
    op.drop_column('orders', 'user_confirmed_at')
    op.drop_column('orders', 'user_tx_hash')
    
    # energy_orders 表
    op.drop_column('energy_orders', 'user_confirmed_at')
    op.drop_column('energy_orders', 'user_tx_hash')

