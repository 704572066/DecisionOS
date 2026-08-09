#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
front = ROOT / "src/frontend/src/main.tsx"
text = front.read_text(encoding="utf-8")

if "type DecisionBoard =" not in text:
    marker = "type MeetingDetails = {\n"
    board_type = """type DecisionBoard = {
  meetingId: string;
  projectId: string;
  contextId: string;
  objective: string;
  status: 'gathering_information'|'negotiating'|'waiting_confirmation'|'ready_to_decide';
  decisionReadiness: number;
  risks: Array<{title:string;summary:string;severity:'low'|'medium'|'high';sourceIds:string[]}>;
  evidence: Array<{id:string;type:string;title:string;summary:string;score:number}>;
  actions: Array<{text:string;sourceIds:string[]}>;
  todos: Array<{text:string;reason:string}>;
  currentConditions: Record<string, unknown>;
  recentEvents: Array<{eventId:string;type:string;sourceText:string;field?:string;previousValue?:string|number|null;value?:string|number|null}>;
  resolvedRisks: string[];
  updatedAt: string;
};

"""
    if marker not in text:
        raise SystemExit("MeetingDetails type marker not found")
    text = text.replace(marker, board_type + marker, 1)

if "const [decisionBoard" not in text:
    marker = "  const [reminders, setReminders] = useState<Reminder[]>([]);\n"
    if marker not in text:
        raise SystemExit("reminders state marker not found")
    state = marker + """  const [decisionBoard, setDecisionBoard] = useState<DecisionBoard | null>(null);
  const [boardLoading, setBoardLoading] = useState(false);
  const [reminderDrawerOpen, setReminderDrawerOpen] = useState(false);
  const [evidenceDrawerOpen, setEvidenceDrawerOpen] = useState(false);
  const [reminderToast, setReminderToast] = useState<Reminder | null>(null);
  const reminderToastTimerRef = useRef<number | null>(null);
"""
    text = text.replace(marker, state, 1)

if "const loadDecisionBoard = async" not in text:
    marker = "  const restoreMeeting = async (targetMeetingId: string) => {\n"
    helpers = """  const loadDecisionBoard = async (targetMeetingId: string, silent = true) => {
    if (!targetMeetingId) return;
    try {
      if (!silent) setBoardLoading(true);
      const board = await fetchJson<DecisionBoard>(`${API}/decision-board/${targetMeetingId}`);
      if (mountedRef.current) setDecisionBoard(board);
    } catch (error) {
      if (!silent) showError(`加载决策看板失败：${getErrorMessage(error)}`);
    } finally {
      if (!silent && mountedRef.current) setBoardLoading(false);
    }
  };

  const showReminderToast = (reminder: Reminder | undefined) => {
    if (!reminder) return;
    if (reminderToastTimerRef.current !== null) {
      window.clearTimeout(reminderToastTimerRef.current);
    }
    setReminderToast(reminder);
    reminderToastTimerRef.current = window.setTimeout(() => {
      setReminderToast(null);
      reminderToastTimerRef.current = null;
    }, 5000);
  };

  const boardStatusLabel = (status?: DecisionBoard['status']) => {
    switch (status) {
      case 'negotiating': return '谈判中';
      case 'waiting_confirmation': return '待确认';
      case 'ready_to_decide': return '可进入决策';
      default: return '信息收集中';
    }
  };

"""
    if marker not in text:
        raise SystemExit("restoreMeeting marker not found")
    text = text.replace(marker, helpers + marker, 1)

old = """    setFinalTranscript(data.transcript || '');
    setPartialTranscript('');
    persistMeetingSession(data.id, data.projectId);
"""
new = """    setFinalTranscript(data.transcript || '');
    setPartialTranscript('');
    persistMeetingSession(data.id, data.projectId);
    await loadDecisionBoard(data.id, true);
"""
if new not in text:
    if old not in text:
        raise SystemExit("restoreMeeting body marker not found")
    text = text.replace(old, new, 1)

old = """      setPartialTranscript('');
      setReminders([]);
      persistMeetingSession(data.id, data.projectId);
"""
new = """      setPartialTranscript('');
      setReminders([]);
      setDecisionBoard(null);
      persistMeetingSession(data.id, data.projectId);
      await loadDecisionBoard(data.id, true);
"""
if new not in text:
    if old not in text:
        raise SystemExit("createMeeting marker not found")
    text = text.replace(old, new, 1)

old = """          } else if (payload.created) {
            setFinalTranscript((current) =>
              [current, payload.segment.text].filter(Boolean).join('\\n')
            );
          }
          break;
"""
new = """          } else if (payload.created) {
            setFinalTranscript((current) =>
              [current, payload.segment.text].filter(Boolean).join('\\n')
            );
          }
          if (meetingId) {
            window.setTimeout(() => loadDecisionBoard(meetingId, true), 120);
          }
          break;
"""
if new not in text:
    if old not in text:
        raise SystemExit("transcript.saved marker not found")
    text = text.replace(old, new, 1)

old = """        case 'reminder.completed':
          setStreamingReminder(null);
          if (payload.reminders) {
            setReminders((current) =>
              [...payload.reminders, ...current].slice(0, 5)
            );
          }
          break;
"""
new = """        case 'reminder.completed':
          setStreamingReminder(null);
          if (payload.reminders) {
            setReminders((current) =>
              [...payload.reminders, ...current].slice(0, 5)
            );
            showReminderToast(payload.reminders[0]);
          }
          if (meetingId) loadDecisionBoard(meetingId, true);
          break;
"""
if new not in text:
    if old not in text:
        raise SystemExit("reminder.completed marker not found")
    text = text.replace(old, new, 1)

if 'className="decision-surface realtime-column"' not in text:
    start = text.find('        <section className="reminder-panel realtime-column">')
    if start == -1:
        raise SystemExit("reminder panel start not found")
    end_marker = "        </section>\n      </div>\n"
    end = text.find(end_marker, start)
    if end == -1:
        raise SystemExit("reminder panel end not found")
    end += len("        </section>\n")
    replacement = """        <section className="decision-surface realtime-column">
          <div className="panel-title">
            <div>
              <span className="eyebrow">Decision Board</span>
              <h2>当前决策状态</h2>
            </div>
            <button className="link-button" onClick={() => meetingId && loadDecisionBoard(meetingId, false)} disabled={!meetingId || boardLoading}>
              {boardLoading ? '刷新中…' : '刷新'}
            </button>
          </div>

          {!decisionBoard ? (
            <div className="decision-board-empty">创建会议后，Decision Board 会持续维护当前目标、风险和下一步行动。</div>
          ) : (
            <div className="decision-board-scroll">
              <div className="decision-board-overview">
                <span className="board-label">当前目标</span>
                <strong>{decisionBoard.objective || '尚未识别明确目标'}</strong>
                <div className="decision-board-status-row">
                  <div><span>状态</span><strong>{boardStatusLabel(decisionBoard.status)}</strong></div>
                  <div><span>决策成熟度</span><strong>{decisionBoard.decisionReadiness}</strong></div>
                </div>
                <div className="readiness-track"><div className="readiness-value" style={{width: `${decisionBoard.decisionReadiness}%`}} /></div>
              </div>

              <section className="board-section">
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
              </section>

              <section className="board-section">
                <div className="board-section-title"><strong>下一步</strong></div>
                <ol className="board-actions">
                  {decisionBoard.actions.slice(0, 2).map((action) => <li key={action.text}>{action.text}</li>)}
                </ol>
              </section>

              <section className="board-section">
                <div className="board-section-title"><strong>待确认</strong></div>
                {decisionBoard.todos.slice(0, 3).map((todo) => (
                  <div className="board-todo" key={todo.text}><span>□</span><span>{todo.text}</span></div>
                ))}
              </section>

              <div className="decision-board-links">
                <button className="secondary-button" onClick={() => setReminderDrawerOpen(true)}>
                  查看提醒 {reminders.length ? `(${reminders.length})` : ''}
                </button>
                <button className="secondary-button" onClick={() => setEvidenceDrawerOpen(true)}>
                  查看依据 ({decisionBoard.evidence.length})
                </button>
              </div>
            </div>
          )}

          {streamingReminder && (
            <div className="board-generating">AI 正在更新判断{streamingTtftMs !== null && <small> · 首字 {Math.round(streamingTtftMs)}ms</small>}</div>
          )}
        </section>
"""
    text = text[:start] + replacement + text[end:]

if 'className="reminder-toast"' not in text:
    marker = "      {decisionCandidate && (\n"
    if marker not in text:
        raise SystemExit("decisionCandidate modal marker not found")
    overlays = """      {reminderToast && (
        <button className="reminder-toast" onClick={() => {setReminderToast(null); setReminderDrawerOpen(true);}}>
          <span className={`toast-icon ${reminderToast.type === 'risk' ? 'risk' : ''}`}>{reminderToast.type === 'risk' ? '!' : 'AI'}</span>
          <span><strong>{reminderToast.title}</strong><small>{reminderToast.summary}</small></span>
        </button>
      )}

      {reminderDrawerOpen && (
        <div className="side-drawer-backdrop" onMouseDown={() => setReminderDrawerOpen(false)}>
          <aside className="side-drawer" onMouseDown={(event) => event.stopPropagation()}>
            <div className="drawer-header"><div><span className="eyebrow">AI Reminder</span><h2>最近提醒</h2></div><button className="link-button" onClick={() => setReminderDrawerOpen(false)}>关闭</button></div>
            <div className="drawer-scroll">
              {reminders.length === 0 && <p className="placeholder">当前没有历史提醒。</p>}
              {reminders.map((reminder, index) => (
                <article className="drawer-reminder" key={`${reminder.source.id}-${index}`}>
                  <strong>{reminder.title}</strong>
                  <p>{reminder.summary}</p>
                  {reminder.suggestion && <p><b>建议：</b>{reminder.suggestion}</p>}
                  <button onClick={() => {setReminderDrawerOpen(false); createDecisionCandidate(reminder);}} disabled={candidateBusy}>生成决策</button>
                </article>
              ))}
            </div>
          </aside>
        </div>
      )}

      {evidenceDrawerOpen && decisionBoard && (
        <div className="side-drawer-backdrop" onMouseDown={() => setEvidenceDrawerOpen(false)}>
          <aside className="side-drawer" onMouseDown={(event) => event.stopPropagation()}>
            <div className="drawer-header"><div><span className="eyebrow">Evidence</span><h2>决策依据</h2></div><button className="link-button" onClick={() => setEvidenceDrawerOpen(false)}>关闭</button></div>
            <div className="drawer-scroll">
              {decisionBoard.evidence.map((item) => (
                <article className="evidence-card" key={item.id}>
                  <div className="evidence-meta"><span>{item.type}</span><span>{Math.round(item.score * 100)}%</span></div>
                  <strong>{item.title}</strong><p>{item.summary}</p>
                </article>
              ))}
            </div>
          </aside>
        </div>
      )}

"""
    text = text.replace(marker, overlays + marker, 1)

front.write_text(text, encoding="utf-8")
print("Sprint 3-2.3 patch applied:", front)
