#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
front = ROOT / 'src/frontend/src/main.tsx'
text = front.read_text(encoding='utf-8')

start_marker = '      {decisionCandidate && ('
footer_marker = "      <footer className={messageType === 'error' ? 'error-message' : ''}>"

start = text.find(start_marker)
end = text.find(footer_marker)

if start < 0:
    raise SystemExit('Decision Candidate block start not found')
if end < 0 or end <= start:
    raise SystemExit('Footer marker not found after Decision Candidate block')

replacement = '''      {decisionCandidate && (
        <div
          className="decision-modal-backdrop"
          role="presentation"
          onMouseDown={() => {
            if (!candidateBusy) setDecisionCandidate(null);
          }}
        >
          <section
            className="decision-candidate-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="decision-candidate-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="panel-title">
              <div>
                <span className="eyebrow">Decision Draft</span>
                <h2 id="decision-candidate-title">决策草案</h2>
              </div>
              <button
                className="link-button"
                onClick={() => setDecisionCandidate(null)}
                disabled={candidateBusy}
              >
                取消
              </button>
            </div>

            <label>
              标题
              <input
                value={candidateTitle}
                onChange={(event) => setCandidateTitle(event.target.value)}
              />
            </label>

            <label>
              决策内容
              <textarea
                rows={4}
                value={candidateStatement}
                onChange={(event) => setCandidateStatement(event.target.value)}
              />
            </label>

            {decisionCandidate.risks.length > 0 && (
              <div className="candidate-block">
                <strong>风险</strong>
                <ul>
                  {decisionCandidate.risks.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="candidate-block">
              <strong>依据</strong>
              <ul>
                {decisionCandidate.evidence.map((item) => (
                  <li key={item.id}>
                    {item.title}
                    <small> · {item.type} · {Math.round(item.score * 100)}%</small>
                  </li>
                ))}
              </ul>
            </div>

            {decisionCandidate.suggestedTasks.length > 0 && (
              <div className="candidate-block">
                <strong>建议后续事项</strong>
                <ul>
                  {decisionCandidate.suggestedTasks.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="candidate-actions">
              <button
                onClick={confirmDecisionCandidate}
                disabled={
                  candidateBusy ||
                  !candidateTitle.trim() ||
                  !candidateStatement.trim()
                }
              >
                {candidateBusy ? '处理中…' : '确认决策'}
              </button>
            </div>
          </section>
        </div>
      )}

'''

front.write_text(text[:start] + replacement + text[end:], encoding='utf-8')
print('Sprint 3-1.1 JSX hotfix applied:', front)
