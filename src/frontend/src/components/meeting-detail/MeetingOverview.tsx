import type {DecisionMemory} from '../../types/decision';
import type {MeetingHistoryDetail, MeetingSummaryResult} from '../../types/meeting';

type MeetingOverviewProps = {detail: MeetingHistoryDetail; summary: MeetingSummaryResult | null; memories: DecisionMemory[]; summaryBusy: boolean; onGenerateSummary: () => void};

export function MeetingOverview({detail, summary, memories, summaryBusy, onGenerateSummary}: MeetingOverviewProps) {
  const snapshot = detail.snapshot;
  if (!snapshot) return null;
  const activeMemories = memories.filter(item => item.status === 'active');
  return <div className="meeting-overview">
    <section className="meeting-overview-section"><div className="meeting-overview-heading"><div><span className="section-label">Summary</span><h2>会议摘要</h2></div>{!summary && <button className="secondary-button" onClick={onGenerateSummary} disabled={summaryBusy}>{summaryBusy ? '生成中…' : '生成总结'}</button>}</div>{summary ? <p className="meeting-summary-text">{summary.summary}</p> : <p className="placeholder">会议已经固化，但尚未生成结构化总结。</p>}</section>
    <section className="meeting-overview-section"><span className="section-label">Outcomes</span><h2>关键结果</h2>{summary?.keyFacts.length ? <ul className="meeting-outcome-list">{summary.keyFacts.map((item,index) => <li key={index}>{item.text}</li>)}</ul> : <p className="placeholder">没有记录明确的关键结果。</p>}</section>
    <section className="meeting-overview-section"><span className="section-label">Decisions</span><h2>会议决策</h2>{summary?.decisions.length ? <><ul className="meeting-decision-list">{summary.decisions.map((item,index) => <li key={index}>{item.text}</li>)}</ul>{activeMemories.length > 0 && <p className="memory-confirmed">✓ 已沉淀 {activeMemories.length} 条有效决策记忆</p>}</> : <p className="placeholder">本次会议未形成明确决策。</p>}</section>
    <div className="meeting-overview-two-column"><section className="meeting-overview-section"><span className="section-label">Actions</span><h2>后续行动</h2>{summary?.actionItems.length ? <ul className="meeting-action-list">{summary.actionItems.map((item,index) => <li key={index}>{item.text}</li>)}</ul> : <p className="placeholder">本次会议没有记录后续行动。</p>}</section><section className="meeting-overview-section"><span className="section-label">Open Issues</span><h2>未解决问题</h2>{summary?.openIssues.length ? <ul className="meeting-issue-list">{summary.openIssues.map((item,index) => <li key={index}>{item.text}</li>)}</ul> : <p className="placeholder">没有记录未解决问题。</p>}</section></div>
    <section className="meeting-overview-section"><span className="section-label">Evidence</span><h2>主要依据</h2>{snapshot.evidence.length ? <div className="meeting-evidence-preview">{snapshot.evidence.slice(0,3).map(item => <article key={item.id}><strong>{item.title}</strong><small>{item.type} · {Math.round(item.score * 100)}%</small></article>)}</div> : <p className="placeholder">本次会议没有记录决策依据。</p>}</section>
  </div>;
}
