from __future__ import annotations
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.context.extractor import topics,entities,facts,constraints,keywords
from app.context.models import BusinessContext,ContextMetadata,ContextReference,TranscriptCleaningMetadata
from app.context.normalizer import clean_and_normalize,normalize,recent_window
from app.models.entities import KnowledgeItem,Meeting,Project

class ContextBuilder:
    def __init__(self,default_max_characters=1600,max_references=8):
        self.default_max_characters=default_max_characters
        self.max_references=max_references
    def build_for_meeting(self,db:Session,meeting:Meeting,objective="",max_characters=None):
        project=db.get(Project,meeting.project_id)
        return self.build(db,project_id=meeting.project_id,meeting_id=meeting.id,transcript=meeting.transcript or "",objective=objective or (project.business_goal if project else ""),max_characters=max_characters)
    def build(self,db:Session,*,project_id,transcript,meeting_id=None,objective="",max_characters=None):
        project=db.get(Project,project_id)
        raw_full=normalize(transcript)
        raw_window=recent_window(raw_full,max_characters or self.default_max_characters)
        cleaning=clean_and_normalize(raw_window)
        clean_window=recent_window(cleaning.clean_text,max_characters or self.default_max_characters)
        topic_values=topics(clean_window)
        fact_values=facts(clean_window)
        entity_values=entities(clean_window)
        constraint_values=constraints(clean_window)
        keyword_values=keywords(clean_window,topic_values,fact_values)
        refs=self._refs(db,project_id,topic_values,keyword_values)
        return BusinessContext(
            contextId="context-"+uuid4().hex[:16],
            projectId=project_id,meetingId=meeting_id,
            intent=self._intent(topic_values,objective),
            currentObjective=objective or (project.business_goal if project else ""),
            transcriptWindow=raw_window,
            cleanTranscriptWindow=clean_window,
            topics=topic_values,entities=entity_values,keywords=keyword_values,
            facts=fact_values,constraints=constraint_values,references=refs,
            metadata=ContextMetadata(
                transcriptCharacters=len(raw_full),
                analyzedCharacters=len(raw_window),
                cleanTranscriptCharacters=len(clean_window),
                cleaning=TranscriptCleaningMetadata(**cleaning.metadata()),
            ),
        )
    def _refs(self,db,project_id,topics_value,keywords_value):
        signals=[*topics_value,*keywords_value[:12]]
        scored=[]
        for item in db.scalars(select(KnowledgeItem).where(KnowledgeItem.project_id==project_id)).all():
            searchable=(item.title+"\n"+item.content).lower()
            hits=sum(1 for x in signals if x and x.lower() in searchable)
            if hits: scored.append((min(1,.35+hits*.1),item))
        scored.sort(key=lambda x:(x[0],x[1].created_at),reverse=True)
        return [ContextReference(objectType=i.object_type,objectId=i.source_id or i.id,title=i.title,summary=i.content,sourceType=i.source_type,relevanceScore=score) for score,i in scored[:self.max_references]]
    @staticmethod
    def _intent(topic_values,objective):
        if objective: return f"围绕“{objective}”识别风险、历史依据与待确认事项"
        return f"分析当前会议中的{'、'.join(topic_values[:4])}议题" if topic_values else "理解当前会议内容并识别需要关注的业务信息"

context_builder=ContextBuilder()
