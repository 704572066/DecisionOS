"""Remove knowledge created by the retired demo seed endpoint.

Revision ID: 20260819_05
Revises: 20260819_04
"""
from alembic import op

revision = "20260819_05"
down_revision = "20260819_04"
branch_labels = None
depends_on = None


LEGACY_DEMO_TITLES = (
    "历史同类客户成交复盘",
    "客户A历史付款记录",
    "公司项目利润率规则",
    "历史账期风险决策",
)


def upgrade():
    # Match the complete legacy seed signature so user-created knowledge with a
    # similar title is not removed. The old seed rows never had a source_id.
    op.execute("""
        DELETE FROM knowledge_items
        WHERE COALESCE(source_id, '') = ''
          AND (
            (title = '历史同类客户成交复盘'
             AND content = '去年同类型客户初始要求降价20%，最终成交折扣为8%。'
             AND source_type = 'document')
            OR
            (title = '客户A历史付款记录'
             AND content = '客户A过去合同平均付款周期为90天，曾出现一次逾期。'
             AND source_type = 'crm')
            OR
            (title = '公司项目利润率规则'
             AND content = '软件项目目标毛利率不得低于18%；超过10%的折扣必须评估付款周期。'
             AND source_type = 'policy')
            OR
            (title = '历史账期风险决策'
             AND content = '对付款周期超过120天的客户，必须增加担保或分阶段收款。'
             AND source_type = 'decision')
          )
    """)


def downgrade():
    # Retired demo data must not be recreated on downgrade.
    pass

