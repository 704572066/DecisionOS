import type {DecisionMemory} from '../types/decision';
import type {MeetingHistoryDetail, MeetingSummaryResult} from '../types/meeting';
import {MeetingDetailHeader} from '../components/meeting-detail/MeetingDetailHeader';
import {MeetingOverview} from '../components/meeting-detail/MeetingOverview';

type MeetingDetailPageProps = {detail: MeetingHistoryDetail | null; summary: MeetingSummaryResult | null; memories: DecisionMemory[]; summaryBusy: boolean; onBack: () => void; onGenerateSummary: () => void};

export function MeetingDetailPage({detail, summary, memories, summaryBusy, onBack, onGenerateSummary}: MeetingDetailPageProps) {
  if (!detail) return <section className="meeting-detail-page"><button className="link-button meeting-detail-back" onClick={onBack}>← 返回会议列表</button><p className="placeholder meeting-detail-loading">正在加载会议详情…</p></section>;
  return <section className="meeting-detail-page"><button className="link-button meeting-detail-back" onClick={onBack}>← 返回会议列表</button><MeetingDetailHeader detail={detail}/><nav className="meeting-detail-tabs" aria-label="会议详情"><button className="active">Overview</button><button disabled>Decisions</button><button disabled>Transcript</button><button disabled>AI Activity</button></nav>{!detail.snapshot ? <section className="meeting-detail-not-finalized"><h2>会议尚未固化</h2><p>会议已经结束，但 Final Snapshot 尚未完成，部分历史内容可能仍在处理中。</p></section> : <MeetingOverview detail={detail} summary={summary} memories={memories} summaryBusy={summaryBusy} onGenerateSummary={onGenerateSummary}/>}</section>;
}
