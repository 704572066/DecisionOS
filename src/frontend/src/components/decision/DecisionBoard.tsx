import type {DecisionBoard as DecisionBoardModel} from '../../types/decision';

type DecisionBoardProps = {
  board: DecisionBoardModel | null; loading: boolean; meetingId: string; reminderCount: number;
  streaming: boolean; streamingTtftMs: number | null;
  onRefresh: () => void; onOpenReminders: () => void; onOpenEvidence: () => void;
};

export function DecisionBoard({board, loading, meetingId, reminderCount, streaming, streamingTtftMs, onRefresh, onOpenReminders, onOpenEvidence}: DecisionBoardProps) {
  return <section className="decision-surface realtime-column">
    <div className="panel-title"><div><span className="eyebrow">Decision Board</span><h2>当前决策状态</h2></div><button className="link-button" onClick={onRefresh} disabled={!meetingId || loading}>{loading ? '刷新中…' : '刷新'}</button></div>
    {!board ? <div className="decision-board-empty">创建会议后，Decision Board 会持续维护当前目标、风险和下一步行动。</div> : <div className="decision-board-scroll">
      <div className="decision-board-overview"><span className="board-label">当前目标</span><strong>{board.objective || '尚未识别明确目标'}</strong></div>
      <section className="board-section priority-layer"><div className="board-section-title"><strong>🔴 当前关注</strong></div>{board.risks.slice(0, 2).map(risk => <article key={`${risk.title}-${risk.summary}`} className={`board-risk signal-risk severity-${risk.severity}`}><span className="risk-dot" /><div><strong>{risk.title}</strong><p>{risk.summary}</p></div></article>)}</section>
      <section className="board-section priority-layer"><div className="board-section-title"><strong>🟡 下一步行动</strong></div><ol className="board-actions">{board.actions.slice(0, 3).map(action => <li key={action.text}>{action.text}</li>)}</ol></section>
      <div className="decision-board-links"><button className="secondary-button" onClick={onOpenReminders}>查看提醒 {reminderCount ? `(${reminderCount})` : ''}</button><button className="secondary-button" onClick={onOpenEvidence}>查看依据 ({board.evidence.length})</button></div>
    </div>}
    {streaming && <div className="board-generating">AI 正在更新判断{streamingTtftMs !== null && <small> · 首字 {Math.round(streamingTtftMs)}ms</small>}</div>}
  </section>;
}
