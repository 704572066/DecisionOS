from __future__ import annotations
import re
from app.decision_board.models import BoardRisk,BoardEvidence,BoardAction,BoardTodo,DecisionBoard
from app.runtime.models import RuntimeState
class DecisionBoardEngine:
    def build(self,state:RuntimeState)->DecisionBoard:
        risks=self._risks(state); evidence=self._evidence(state); actions=self._actions(state); todos=self._todos(state,risks); confidence=self._confidence(state,evidence); status=self._status(state,risks,confidence)
        return DecisionBoard(meetingId=state.meetingId,projectId=state.projectId,contextId=state.contextId,objective=state.objective,status=status,confidence=confidence,risks=risks[:3],evidence=evidence[:5],actions=actions[:3],todos=todos[:5],updatedAt=state.updatedAt,diagnostics={"retrievalMode":state.retrievalMode,"reminderCount":len(state.reminders),"evidenceCount":len(state.rerankedEvidence)})
    def _risks(self,state):
        out=[]; seen=set()
        for r in state.reminders:
            if r.get("type")!="risk": continue
            title=(r.get("title") or "当前风险").strip(); summary=(r.get("summary") or "").strip(); key=self._norm(title+summary)
            if not key or key in seen: continue
            seen.add(key); c=float(r.get("confidence") or r.get("relevanceScore") or 0); sev="high" if c>=.85 else "medium" if c>=.6 else "low"
            out.append(BoardRisk(title=title,summary=summary,severity=sev,sourceIds=[str(x.get("id")) for x in (r.get("sources") or []) if x.get("id")][:3]))
        order={"high":3,"medium":2,"low":1}; out.sort(key=lambda x:order[x.severity],reverse=True); return out
    def _evidence(self,state):
        out=[]; seen=set()
        for x in state.rerankedEvidence:
            oid=str(x.get("objectId") or x.get("itemId") or "")
            if not oid or oid in seen: continue
            seen.add(oid); out.append(BoardEvidence(id=oid,type=x.get("sourceType") or x.get("objectType") or "knowledge",title=x.get("title") or "企业依据",summary=x.get("summary") or "",score=float(x.get("rerankScore") or x.get("score") or 0)))
        out.sort(key=lambda x:x.score,reverse=True); return out
    def _actions(self,state):
        out=[]; seen=set()
        for r in state.reminders:
            s=(r.get("suggestion") or "").strip(); k=self._norm(s)
            if not k or k in seen: continue
            seen.add(k); out.append(BoardAction(text=s,sourceIds=[str(x.get("id")) for x in (r.get("sources") or []) if x.get("id")][:3]))
        return out
    def _todos(self,state,risks):
        out=[]; seen=set()
        def add(t,reason):
            k=self._norm(t)
            if k and k not in seen: seen.add(k); out.append(BoardTodo(text=t,reason=reason))
        if any(t in state.topics for t in ("价格","利润")): add("确认当前方案的最低可接受毛利率与折扣边界","当前会议涉及价格/利润条件。")
        if "付款" in state.topics: add("确认可接受付款周期及对应风险控制条件","当前会议涉及付款周期。")
        for c in state.constraints:
            d=(c.get("description") or "").strip()
            if d: add("确认约束："+d,"Context Builder 识别到尚需确认的约束。")
        if any(x.severity=="high" for x in risks): add("由负责人确认是否继续按当前条件推进谈判","当前存在高优先级风险，AI 不替代最终决策。")
        return out
    def _confidence(self,state,evidence):
        s=20+(15 if state.objective else 0)+(10 if state.canonicalContext else 0)+min(15,len(state.facts)*5)+min(25,len(evidence)*6)+(7 if any(x.type=="policy" for x in evidence) else 0)+(5 if any(x.type=="decision" for x in evidence) else 0)+(5 if state.reminders else 0)
        return max(0,min(100,round(s)))
    def _status(self,state,risks,confidence):
        if not state.canonicalContext or confidence<45:return "gathering_information"
        if any(x.severity=="high" for x in risks):return "negotiating"
        if confidence>=80 and state.reminders:return "ready_to_decide"
        return "waiting_confirmation"
    def _norm(self,t): return re.sub(r"[\s，。；：、,.!?！？:;]+","",t).lower()
decision_board_engine=DecisionBoardEngine()
