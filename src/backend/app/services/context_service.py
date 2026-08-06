from sqlalchemy.orm import Session
from app.context.service import build_meeting_context
from app.models.entities import Meeting

def analyze_meeting(db:Session,meeting:Meeting)->dict:
 context=build_meeting_context(db,meeting)
 reminders=[{"title":r.title,"summary":r.summary,"source":{"type":r.sourceType or r.objectType,"id":r.objectId},"relevanceScore":r.relevanceScore} for r in context.references[:5]]
 if not reminders: reminders=[{"title":"暂未发现高相关历史信息","summary":"当前内容已构建为 Context。继续输入更多业务细节后再次分析。","source":{"type":"system","id":"context-builder-v0.1"},"relevanceScore":.1}]
 return {"meetingId":meeting.id,"topics":context.topics,"reminders":reminders,"context":context.model_dump(mode='json')}
