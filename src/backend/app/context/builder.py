from __future__ import annotations
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.context.extractor import topics,entities,facts,constraints,keywords
from app.context.models import BusinessContext,ContextMetadata,ContextReference
from app.context.normalizer import normalize,recent_window
from app.models.entities import KnowledgeItem,Meeting,Project

class ContextBuilder:
 def __init__(self,default_max_characters=1600,max_references=8):
  self.default_max_characters=default_max_characters; self.max_references=max_references
 def build_for_meeting(self,db:Session,meeting:Meeting,objective='',max_characters=None):
  p=db.get(Project,meeting.project_id)
  return self.build(db,project_id=meeting.project_id,meeting_id=meeting.id,transcript=meeting.transcript or '',objective=objective or (p.business_goal if p else ''),max_characters=max_characters)
 def build(self,db:Session,*,project_id,transcript,meeting_id=None,objective='',max_characters=None):
  p=db.get(Project,project_id); full=normalize(transcript); win=recent_window(full,max_characters or self.default_max_characters)
  t=topics(win); f=facts(win); e=entities(win); c=constraints(win); k=keywords(win,t,f); refs=self._refs(db,project_id,t,k)
  return BusinessContext(contextId='context-'+uuid4().hex[:16],projectId=project_id,meetingId=meeting_id,intent=self._intent(t,objective),currentObjective=objective or (p.business_goal if p else ''),transcriptWindow=win,topics=t,entities=e,keywords=k,facts=f,constraints=c,references=refs,metadata=ContextMetadata(transcriptCharacters=len(full),analyzedCharacters=len(win)))
 def _refs(self,db,project_id,t,k):
  signals=[*t,*k[:12]]; scored=[]
  for item in db.scalars(select(KnowledgeItem).where(KnowledgeItem.project_id==project_id)).all():
   s=(item.title+'\n'+item.content).lower(); hits=sum(1 for x in signals if x.lower() in s)
   if hits: scored.append((min(1,.35+hits*.1),item))
  scored.sort(key=lambda x:(x[0],x[1].created_at),reverse=True)
  return [ContextReference(objectType=i.object_type,objectId=i.source_id or i.id,title=i.title,summary=i.content,sourceType=i.source_type,relevanceScore=sc) for sc,i in scored[:self.max_references]]
 @staticmethod
 def _intent(t,objective):
  if objective:return f'围绕“{objective}”识别风险、历史依据与待确认事项'
  return f"分析当前会议中的{'、'.join(t[:4])}议题" if t else '理解当前会议内容并识别需要关注的业务信息'
context_builder=ContextBuilder()
