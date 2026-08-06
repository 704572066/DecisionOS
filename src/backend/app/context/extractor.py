from __future__ import annotations
import re
from collections import Counter
from app.context.models import ContextConstraint, ContextEntity, ContextFact

TOPICS={
 "价格":("价格","降价","折扣","报价","费用","成本"),
 "付款":("付款","账期","回款","预付款","尾款","分期"),
 "利润":("利润","毛利","利润率","毛利率"),
 "交付":("交付","上线","验收","工期","排期","延期"),
 "合同":("合同","条款","签约","违约","续约"),
 "风险":("风险","逾期","违约","坏账","担保","损失"),
 "客户":("客户","甲方","采购方","用户方"),
 "资源":("人员","资源","人力","研发","实施"),
}
CONSTRAINTS={
 "价格约束":("最低价格","最高折扣","不得低于","预算上限"),
 "时间约束":("必须在","截止","最晚","延期","交付日期"),
 "付款约束":("账期不得","必须预付","分阶段收款","担保"),
 "合规约束":("合规","审批","授权","保密","监管"),
}
PERCENT=re.compile(r'(?<!\d)(\d+(?:\.\d+)?)\s*%')
DURATION=re.compile(r'(?<!\d)(\d+)\s*(天|个月|月|周|小时)')
MONEY=re.compile(r'(?<!\d)(\d+(?:\.\d+)?)\s*(万元|万|亿元|元|人民币|美元)')
DATE=re.compile(r'(?<!\d)(?:\d{4}年)?\d{1,2}月\d{1,2}日|(?<!\d)\d{4}-\d{1,2}-\d{1,2}')
ENTITY=re.compile(r'([\u4e00-\u9fffA-Za-z0-9]{2,24}(?:公司|集团|项目|部门|团队|客户|供应商|委员会))')
TOKEN=re.compile(r'[\u4e00-\u9fff]{2,8}')
STOP={"我们","你们","他们","这个","那个","目前","今天","现在","可以","需要","希望","已经","进行","相关","一个","如果","因为","所以","客户","项目","会议","问题","内容"}

def topics(text): return sorted([k for k,v in TOPICS.items() if any(x in text for x in v)])
def entities(text):
 c=Counter(m.group(1) for m in ENTITY.finditer(text)); out=[]
 for name,n in c.most_common(12):
  typ='organization' if name.endswith(('公司','集团','部门','团队','委员会')) else ('project' if name.endswith('项目') else ('customer' if name.endswith('客户') else ('supplier' if name.endswith('供应商') else 'unknown')))
  out.append(ContextEntity(name=name,entityType=typ,confidence=.75,mentions=n))
 return out

def _sentence(text,s,e):
 left=max(text.rfind('。',0,s),text.rfind('！',0,s),text.rfind('？',0,s),text.rfind('\n',0,s))
 cand=[i for i in (text.find('。',e),text.find('！',e),text.find('？',e),text.find('\n',e)) if i>=0]
 right=min(cand) if cand else len(text)
 return text[left+1:right+1].strip()

def facts(text):
 out=[]; seen=set()
 def add(raw,typ,val,s,e):
  key=(typ,val)
  if key in seen:return
  seen.add(key); out.append(ContextFact(text=raw,factType=typ,normalizedValue=val,sourceText=_sentence(text,s,e)))
 for m in PERCENT.finditer(text): add(m.group(0),'percentage',m.group(1)+'%',m.start(),m.end())
 for m in DURATION.finditer(text): add(m.group(0),'duration',m.group(1)+m.group(2),m.start(),m.end())
 for m in MONEY.finditer(text): add(m.group(0),'amount',m.group(1)+m.group(2),m.start(),m.end())
 for m in DATE.finditer(text): add(m.group(0),'date',m.group(0),m.start(),m.end())
 return out[:20]

def constraints(text):
 out=[]
 for typ,terms in CONSTRAINTS.items():
  hits=[x for x in terms if x in text]
  if hits: out.append(ContextConstraint(constraintType=typ,description='、'.join(hits),severity='warning'))
 return out

def keywords(text,topic_values,fact_values):
 c=Counter(x for x in TOKEN.findall(text) if x not in STOP); out=[]
 for x in [*topic_values,*[(f.normalizedValue or f.text) for f in fact_values],*[x for x,_ in c.most_common(20)]]:
  if x not in out: out.append(x)
 return out[:24]
