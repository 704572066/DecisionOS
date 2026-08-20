import type {MeetingHistoryItem} from '../types/meeting';

type MeetingHistoryPageProps = {items: MeetingHistoryItem[]; onOpen: (id: string) => void};

export function MeetingHistoryPage({items, onOpen}: MeetingHistoryPageProps) {
  return <section className="history-page">
    <header className="history-heading"><span className="eyebrow">Meetings</span><h1>历史会议</h1><p>查看已经结束和固化的会议记录、总结与决策结果。</p></header>
    <div className="meeting-history-list">{items.length === 0 ? <p className="placeholder">还没有已结束的会议。</p> : items.map(item => <button className="meeting-history-row" key={item.id} onClick={() => onOpen(item.id)}><span className={`knowledge-status ${item.status === 'finalized' ? 'ready' : 'processing'}`}>{item.status === 'finalized' ? '已固化' : '待固化'}</span><span><strong>{item.title}</strong><small>{new Date(item.startedAt).toLocaleString()}</small></span><span className="meeting-history-arrow">→</span></button>)}</div>
  </section>;
}
