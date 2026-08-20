import type {MeetingDetails, MeetingHistoryItem} from '../types/meeting';

type MeetingsPageProps = {
  currentMeeting: MeetingDetails | null;
  transcriptCount: number;
  history: MeetingHistoryItem[];
  loading: boolean;
  creating: boolean;
  onStart: () => void;
  onContinue: () => void;
  onOpenHistory: (id: string) => void;
  onViewAllHistory: () => void;
};

function meetingDate(item: MeetingHistoryItem): string {
  const value = item.finalizedAt || item.endedAt || item.startedAt;
  return new Intl.DateTimeFormat('zh-CN', {year: 'numeric', month: 'short', day: 'numeric'}).format(new Date(value));
}

export function MeetingsPage(props: MeetingsPageProps) {
  return <section className="meetings-page">
    <header className="meetings-heading"><div><span className="eyebrow">Meetings</span><h1>会议</h1><p>开始、继续或回顾工作空间中的会议。</p></div>{!props.currentMeeting && <button onClick={props.onStart} disabled={props.creating}>{props.creating ? '创建中…' : 'Start meeting'}</button>}</header>

    <section className="meetings-section"><div className="meetings-section-heading"><div><span className="home-section-label">Active</span><h2>当前会议</h2></div></div>
      {props.currentMeeting ? <article className="active-meeting-card"><div className="active-meeting-status"><span />In progress</div><div><h3>{props.currentMeeting.title}</h3><p>{props.transcriptCount} 条转写 · Decision Board 持续更新中</p></div><button onClick={props.onContinue}>Continue →</button></article> : <div className="meetings-empty"><div><strong>当前没有进行中的会议</strong><p>创建会议后，DecisionOS 会跟踪转写、风险、依据和决策。</p></div><button onClick={props.onStart} disabled={props.creating}>{props.creating ? '创建中…' : 'Start meeting'}</button></div>}
    </section>

    <section className="meetings-section"><div className="meetings-section-heading"><div><span className="home-section-label">History</span><h2>历史会议</h2></div><button className="link-button" onClick={props.onViewAllHistory}>View all</button></div>
      {props.loading ? <p className="home-muted">正在加载…</p> : props.history.length ? <div className="meetings-history-list">{props.history.slice(0, 6).map(item => <button key={item.id} onClick={() => props.onOpenHistory(item.id)}><span className={`meeting-history-state ${item.status}`}>{item.status === 'finalized' ? 'Completed' : 'Ended'}</span><span><strong>{item.title}</strong><small>{meetingDate(item)}</small></span><span>›</span></button>)}</div> : <div className="meetings-empty"><div><strong>还没有历史会议</strong><p>结束并归档一场会议后，它会固定保存在这里。</p></div></div>}
    </section>
  </section>;
}
