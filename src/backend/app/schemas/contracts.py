from pydantic import BaseModel,Field
class ProjectCreate(BaseModel):
 name:str; businessGoal:str=''
class MeetingCreate(BaseModel):
 projectId:str; title:str='未命名会议'
class TranscriptAppend(BaseModel):
 text:str=Field(min_length=1)
class DecisionCreate(BaseModel):
 projectId:str; meetingId:str|None=None; title:str; statement:str; evidenceSummary:str=''; taskTitle:str|None=None; taskObjective:str|None=None; taskOwner:str=''
class ContextBuildRequest(BaseModel):
 projectId:str; meetingId:str|None=None; transcript:str=''; objective:str=''; maxCharacters:int=Field(default=1600,ge=200,le=12000)
