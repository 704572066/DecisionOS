from threading import RLock
from datetime import datetime, timezone
from app.runtime.models import RuntimeState
class RuntimeStateStore:
    def __init__(self): self._states={}; self._lock=RLock()
    def get(self,meeting_id):
        with self._lock: return self._states.get(meeting_id)
    def put(self,state):
        state.updatedAt=datetime.now(timezone.utc)
        with self._lock: self._states[state.meetingId]=state
        return state
    def delete(self,meeting_id):
        with self._lock: self._states.pop(meeting_id,None)
runtime_state_store=RuntimeStateStore()
