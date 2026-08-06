from sqlalchemy.orm import Session
from app.context.builder import context_builder
from app.models.entities import Meeting

def build_meeting_context(db:Session,meeting:Meeting,*,objective='',max_characters=None):
 return context_builder.build_for_meeting(db,meeting,objective=objective,max_characters=max_characters)
