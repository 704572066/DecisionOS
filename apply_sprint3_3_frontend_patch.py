from pathlib import Path

file = Path("src/frontend/src/main.tsx")
text = file.read_text(encoding="utf-8")

old = """<section className="board-section">
                <div className="board-section-title"><strong>现在最值得关注</strong><span>{decisionBoard.risks.length} 项风险</span></div>
                {decisionBoard.risks.length === 0 ? (
                  <div className="board-success">✓ 当前没有未解决的高优先级风险</div>
                ) : decisionBoard.risks.slice(0, 2).map((risk) => (
                  <article key={`${risk.title}-${risk.summary}`} className={`board-risk severity-${risk.severity}`}>
                    <span className="risk-dot" />
                    <div><strong>{risk.title}</strong><p>{risk.summary}</p></div>
                  </article>
                ))}
                {decisionBoard.resolvedRisks.includes('payment_term') && (
                  <div className="board-resolved">✓ 付款条件风险已缓解</div>
                )}
              </section>"""

new = """<section className="board-section priority-layer">
                <div className="board-section-title"><strong>🔴 NOW 当前关注</strong></div>
                {decisionBoard.risks.slice(0, 2).map((risk) => (
                  <article key={`${risk.title}-${risk.summary}`} className={`board-risk signal-risk severity-${risk.severity}`}>
                    <span className="risk-dot" />
                    <div><strong>{risk.title}</strong><p>{risk.summary}</p></div>
                  </article>
                ))}
                {decisionBoard.resolvedRisks.includes('payment_term') && (
                  <div className="board-resolved">✓ 风险解除：付款条件已缓解</div>
                )}
              </section>

              <section className="board-section priority-layer">
                <div className="board-section-title"><strong>🟡 NEXT 下一步行动</strong></div>
                <ol className="board-actions">
                  {decisionBoard.actions.slice(0, 3).map((action) => <li key={action.text}>{action.text}</li>)}
                </ol>
              </section>

              <section className="board-section priority-layer">
                <div className="board-section-title"><strong>⚪ LATER 待确认</strong></div>
                {decisionBoard.todos.slice(0, 3).map((todo) => (
                  <div className="board-todo" key={todo.text}><span>□</span><span>{todo.text}</span></div>
                ))}
              </section>"""

if old not in text:
    raise SystemExit("Decision Board frontend marker not found")

file.write_text(text.replace(old, new), encoding="utf-8")
print("Sprint 3-3 frontend patch applied")
