import type {MeetingHistoryDetail} from '../../types/meeting';

export function MeetingDetailHeader({detail}: {detail: MeetingHistoryDetail}) {
  const {meeting, snapshot} = detail;
  return <header className="meeting-detail-header"><div><span className="eyebrow">Meeting Archive</span><h1>{meeting.title}</h1><div className="meeting-detail-meta"><span className={`knowledge-status ${meeting.status === 'finalized' ? 'ready' : 'processing'}`}>{meeting.status === 'finalized' ? 'Finalized' : 'Ended'}</span><span>开始 {new Date(meeting.startedAt).toLocaleString()}</span>{meeting.endedAt && <span>结束 {new Date(meeting.endedAt).toLocaleString()}</span>}{meeting.finalizedAt && <span>固化 {new Date(meeting.finalizedAt).toLocaleString()}</span>}</div></div>{snapshot && <div className="meeting-detail-objective"><small>会议目标</small><strong>{snapshot.objective || '未识别明确目标'}</strong></div>}</header>;
}
