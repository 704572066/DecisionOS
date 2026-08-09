from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
DecisionStatus=Literal["gathering_information","negotiating","waiting_confirmation","ready_to_decide"]
class BoardRisk(BaseModel):
    title:str; summary:str; severity:Literal["low","medium","high"]="medium"; sourceIds:list[str]=Field(default_factory=list)
class BoardEvidence(BaseModel):
    id:str; type:str; title:str; summary:str=""; score:float=Field(default=0,ge=0,le=1)
class BoardAction(BaseModel):
    text:str; sourceIds:list[str]=Field(default_factory=list)
class BoardTodo(BaseModel):
    text:str; reason:str=""
class DecisionBoard(BaseModel):
    meetingId:str; projectId:str; contextId:str; objective:str=""; status:DecisionStatus="gathering_information"; confidence:int=Field(default=0,ge=0,le=100)
    risks:list[BoardRisk]=Field(default_factory=list); evidence:list[BoardEvidence]=Field(default_factory=list); actions:list[BoardAction]=Field(default_factory=list); todos:list[BoardTodo]=Field(default_factory=list)
    updatedAt:datetime; diagnostics:dict=Field(default_factory=dict)
