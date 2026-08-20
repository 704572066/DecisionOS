import type {Identity} from '../types/auth';
import type {DecisionBoard, DecisionMemory} from '../types/decision';
import type {MeetingDetails, MeetingHistoryItem} from '../types/meeting';

type HomePageProps = {
  identity: Identity;
  currentMeeting: MeetingDetails | null;
  transcriptCount: number;
  board: DecisionBoard | null;
  recentMeetings: MeetingHistoryItem[];
  recentDecisions: DecisionMemory[];
  loading: boolean;
  onStartMeeting: () => void;
  onContinueMeeting: () => void;
  onOpenAttention: () => void;
  onOpenMeeting: (id: string) => void;
  onViewMeetings: () => void;
  onViewDecisions: () => void;
};

function formatDate(value?: string | null): string {
  if (!value) return '';
  return new Intl.DateTimeFormat('zh-CN', {month: 'short', day: 'numeric'}).format(new Date(value));
}

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 11) return '早上好';
  if (hour < 14) return '中午好';
  if (hour < 18) return '下午好';
  return '晚上好';
}

export function HomePage(props: HomePageProps) {
  const policyInterventions = props.board?.reasoning?.interventions;
  const visibleInterventions = (policyInterventions || []).filter(item => item.level !== 'silent').sort((a, b) => b.score - a.score);
  const attention = visibleInterventions[0];
  const fallbackRisk = Array.isArray(policyInterventions) ? undefined : props.board?.risks[0];
  const attentionTitle = attention?.title || fallbackRisk?.title;
  const attentionSummary = attention?.message || fallbackRisk?.summary;
  const attentionLevel = attention?.level === 'interrupt' ? 'HIGH' : attention ? 'ATTENTION' : fallbackRisk?.severity.toUpperCase();
  const name = props.identity.user.username || props.identity.user.email.split('@')[0];

  return <section className="home-page">
    <header className="home-heading"><span className="eyebrow">Decision Workspace Overview</span><h1>{greeting()}，{name}</h1><p>以下是当前最值得关注的工作状态。</p></header>

    <section className="home-current-card">
      <div><span className="home-section-label">Current meeting</span>{props.currentMeeting ? <><h2>{props.currentMeeting.title}</h2><p>In progress · {props.transcriptCount} 条转写</p></> : <><h2>开始一场会议</h2><p>记录对话，让 DecisionOS 持续追踪风险、依据与决策。</p></>}</div>
      <button onClick={props.currentMeeting ? props.onContinueMeeting : props.onStartMeeting}>{props.currentMeeting ? 'Continue →' : 'Start meeting →'}</button>
    </section>

    <div className="home-grid">
      <section className="home-panel home-attention"><div className="home-panel-heading"><div><span className="home-section-label">Needs attention</span><h2>当前关注</h2></div></div>
        {attentionTitle ? <button className="home-attention-item" onClick={props.onOpenAttention}><span className={`home-priority ${attention?.level === 'interrupt' || fallbackRisk?.severity === 'high' ? 'high' : ''}`}>{attentionLevel}</span><strong>{attentionTitle}</strong><p>{attentionSummary}</p><small>View meeting →</small></button> : <div className="home-empty"><strong>当前没有需要主动关注的事项</strong><p>会议产生 surface 或 interrupt 提醒后，会显示在这里。</p></div>}
      </section>

      <section className="home-panel"><div className="home-panel-heading"><div><span className="home-section-label">Recent meetings</span><h2>最近会议</h2></div><button className="link-button" onClick={props.onViewMeetings}>View all</button></div>
        {props.loading ? <p className="home-muted">正在加载…</p> : props.recentMeetings.length ? <div className="home-list">{props.recentMeetings.slice(0, 4).map(meeting => <button key={meeting.id} onClick={() => props.onOpenMeeting(meeting.id)}><span><strong>{meeting.title}</strong><small>{formatDate(meeting.finalizedAt || meeting.endedAt || meeting.startedAt)} · {meeting.status === 'finalized' ? 'Completed' : 'Ended'}</small></span><span>›</span></button>)}</div> : <div className="home-empty"><strong>还没有历史会议</strong><p>结束并归档会议后会显示在这里。</p></div>}
      </section>

      <section className="home-panel"><div className="home-panel-heading"><div><span className="home-section-label">Recent decisions</span><h2>最近决策</h2></div><button className="link-button" onClick={props.onViewDecisions}>View memory</button></div>
        {props.loading ? <p className="home-muted">正在加载…</p> : props.recentDecisions.length ? <div className="home-list">{props.recentDecisions.slice(0, 4).map(decision => <button key={decision.id} onClick={() => props.onOpenMeeting(decision.sourceMeetingId)}><span><strong>{decision.title || decision.decision}</strong><small>{formatDate(decision.effectiveAt || decision.createdAt)} · Historical decision</small></span><span>›</span></button>)}</div> : <div className="home-empty"><strong>还没有决策记忆</strong><p>会议中确认的决策会逐渐沉淀在这里。</p></div>}
      </section>
    </div>
  </section>;
}
