from app.reasoning.general.context import GeneralReasoningContextBuilder
from app.reasoning.general.finding_gate import FindingGate
from app.reasoning.general.models import GeneralFindingCandidate
from app.reasoning.models import Finding
from app.reasoning.shared_finding_merger import SharedFindingMerger
from app.runtime.models import RuntimeState

state = RuntimeState(
    meetingId="m", contextId="c", projectId="p",
    canonicalContext="按8%推进，后来客户只接受10%。",
    decisionFacts={"semanticState": {"commercial": [{
        "domain":"commercial", "field":"discountPercent", "value":10,
        "actor":"customer", "role":"requirement", "status":"confirmed",
        "confidence":.95, "sourceText":"客户只接受10%", "eventId":"e10"
    }]}}, decisionState={"commercial":{"discountPercent":10}},
    recentEvents=[], rerankedEvidence=[]
)
ctx=GeneralReasoningContextBuilder().build(state)

def cand(**kw):
    base=dict(type="decision_risk",domain="general",subject="discountPercent",title="旧8%可能不行",summary="根据旧文本判断",severity="medium",confidence=.9,decisionRelevance=.9,specificity=.9,evidenceDirectness=.9,directlyObserved=True,directlyNeeded=False,evidenceSourceIds=[ctx.contextSourceId],noveltyKey="old-8",suggestedAction="确认")
    base.update(kw); return GeneralFindingCandidate(**base)

d=FindingGate().evaluate(ctx,cand())
assert not d.accepted and d.reason=="conversation_cannot_override_current_state", d

d=FindingGate().evaluate(ctx,cand(type="contradiction", title="18%降价与18%毛利率底线冲突", summary="18%降价直接突破18%毛利率", evidenceSourceIds=["e10"], noveltyKey="bad-metric"))
assert not d.accepted and d.reason=="incompatible_metric_comparison", d

enterprise=Finding(id="p1",type="dependency",status="open",domain="commercial",subject="discountPercent",title="超过10%需付款评估",summary="",severity="high",confidence=.9,sourceIds=[],attributes={"operand":{"domain":"commercial","subject":"paymentTermAssessment","operator":"exists"}},fingerprint="p1")
general=Finding(id="g1",type="gap",status="open",domain="general",subject="paymentTermAssessment",title="缺付款评估",summary="",severity="high",confidence=.9,sourceIds=[],attributes={"reasoningSource":"general","generalFindingType":"missing_information"},fingerprint="g1")
r=SharedFindingMerger().merge(meeting_id="m",context_id="c",enterprise_findings=[enterprise],general_findings=[general])
assert [x.id for x in r.findings]==["p1"]
assert r.diagnostics["suppressedGeneralFindings"][0]["reason"]=="enterprise_dependency_operand_already_covered"
print("PHASE 2.2 GUARDS: OK")
