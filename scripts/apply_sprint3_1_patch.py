#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
main=ROOT/"src/backend/app/main.py"; text=main.read_text(encoding="utf-8")
if "decision_candidate_router" not in text:
    lines=text.splitlines(); pos=0
    for i,line in enumerate(lines):
        if line.startswith("from app.api."): pos=i+1
    lines.insert(pos,"from app.api.decision_candidates import router as decision_candidate_router")
    text="\n".join(lines)+"\n"
    marker=next((m for m in ["app.include_router(ai_reminder_router)","app.include_router(retrieval_admin_router)","app.include_router(router)"] if m in text),None)
    if not marker: raise SystemExit("main.py include_router marker not found")
    text=text.replace(marker,marker+"\napp.include_router(decision_candidate_router)",1)
    main.write_text(text,encoding="utf-8")

front=ROOT/"src/frontend/src/main.tsx"; text=front.read_text(encoding="utf-8")
if "type DecisionCandidate =" not in text:
    marker="type MeetingDetails = {\n"
    block="""type DecisionCandidate = {\n  candidateId: string; projectId: string; meetingId: string; contextId: string;\n  title: string; summary: string; statement: string; reasons: string[]; risks: string[];\n  evidence: Array<{type: string; id: string; title: string; summary: string; score: number}>;\n  suggestedTasks: string[]; status: string;\n};\n\n"""
    if marker not in text: raise SystemExit("MeetingDetails marker not found")
    text=text.replace(marker,block+marker,1)
if "decisionCandidate" not in text:
    marker="  const [reminders, setReminders] = useState<Reminder[]>([]);\n"
    block=marker+"""  const [decisionCandidate, setDecisionCandidate] = useState<DecisionCandidate | null>(null);\n  const [candidateTitle, setCandidateTitle] = useState('');\n  const [candidateStatement, setCandidateStatement] = useState('');\n  const [candidateBusy, setCandidateBusy] = useState(false);\n"""
    if marker not in text: raise SystemExit("reminders state marker not found")
    text=text.replace(marker,block,1)
    marker="  const submitManualText = async () => {\n"
    funcs="""  const createDecisionCandidate = async (reminder: Reminder) => {\n    if (!meetingId) return showError('请先创建会议');\n    try {\n      setCandidateBusy(true);\n      const candidate = await fetchJson<DecisionCandidate>(`${API}/decisions/meetings/${meetingId}/candidate`, {\n        method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({reminder}),\n      });\n      setDecisionCandidate(candidate); setCandidateTitle(candidate.title); setCandidateStatement(candidate.statement);\n    } catch (error) { showError(`生成决策草案失败：${getErrorMessage(error)}`); }\n    finally { setCandidateBusy(false); }\n  };\n\n  const confirmDecisionCandidate = async () => {\n    if (!decisionCandidate) return;\n    try {\n      setCandidateBusy(true);\n      const result = await fetchJson<{decisionId:string;status:string;knowledgeUpdated:boolean}>(`${API}/decisions/confirm`, {\n        method:'POST', headers:{'Content-Type':'application/json'},\n        body:JSON.stringify({candidate:decisionCandidate,title:candidateTitle,statement:candidateStatement}),\n      });\n      setDecisionCandidate(null); showInfo(`决策已确认：${result.decisionId}，企业知识已更新`);\n    } catch (error) { showError(`确认决策失败：${getErrorMessage(error)}`); }\n    finally { setCandidateBusy(false); }\n  };\n\n"""
    if marker not in text: raise SystemExit("submitManualText marker not found")
    text=text.replace(marker,funcs+marker,1)
    marker="""              <small>\n                来源：{reminder.source.type} / {reminder.source.id}\n"""
    action="""              <div className=\"reminder-actions\">\n                <button onClick={() => createDecisionCandidate(reminder)} disabled={candidateBusy}>生成决策</button>\n              </div>\n              <small>\n                来源：{reminder.source.type} / {reminder.source.id}\n"""
    if marker not in text: raise SystemExit("reminder source marker not found")
    text=text.replace(marker,action,1)
    marker="""      <footer className={messageType === 'error' ? 'error-message' : ''}>\n"""
    workspace="""      {decisionCandidate && (\n        <section className=\"decision-candidate-panel\">\n          <div className=\"panel-title\"><div><span className=\"eyebrow\">Decision Draft</span><h2>决策草案</h2></div>\n            <button className=\"link-button\" onClick={() => setDecisionCandidate(null)} disabled={candidateBusy}>取消</button>\n          </div>\n          <label>标题<input value={candidateTitle} onChange={(e) => setCandidateTitle(e.target.value)} /></label>\n          <label>决策内容<textarea rows={4} value={candidateStatement} onChange={(e) => setCandidateStatement(e.target.value)} /></label>\n          {decisionCandidate.risks.length > 0 && <div className=\"candidate-block\"><strong>风险</strong><ul>{decisionCandidate.risks.map((x)=><li key={x}>{x}</li>)}</ul></div>}\n          <div className=\"candidate-block\"><strong>依据</strong><ul>{decisionCandidate.evidence.map((x)=><li key={x.id}>{x.title}<small> · {x.type} · {Math.round(x.score*100)}%</small></li>)}</ul></div>\n          {decisionCandidate.suggestedTasks.length > 0 && <div className=\"candidate-block\"><strong>建议后续事项</strong><ul>{decisionCandidate.suggestedTasks.map((x)=><li key={x}>{x}</li>)}</ul></div>}\n          <div className=\"candidate-actions\"><button onClick={confirmDecisionCandidate} disabled={candidateBusy || !candidateTitle.trim() || !candidateStatement.trim()}>{candidateBusy?'处理中…':'确认决策'}</button></div>\n        </section>\n      )}\n\n"""
    if marker not in text: raise SystemExit("footer marker not found")
    text=text.replace(marker,workspace+marker,1)
    front.write_text(text,encoding="utf-8")
print("Sprint 3-1 patch applied")
