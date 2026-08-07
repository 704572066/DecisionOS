from app.context.extractor import topics,facts,constraints
from app.context.normalizer import recent_window

def test_topics(): assert topics('客户要求降价18%，付款周期延长到180天。')==['付款','价格','客户']
def test_facts():
 vals={x.normalizedValue for x in facts('客户要求降价18%，付款周期延长到180天。')}; assert '18%' in vals and '180天' in vals
def test_constraints():
 vals={x.constraintType for x in constraints('合同要求最晚9月30日交付，必须预付30%。')}; assert '时间约束' in vals and '付款约束' in vals
def test_window(): assert '付款180天' in recent_window('早期。'+'普通内容'*100+'付款180天。',80)
