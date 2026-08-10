from pydantic import BaseModel

class DecisionSignal(BaseModel):
    level: str
    type: str
    title: str
    message: str
