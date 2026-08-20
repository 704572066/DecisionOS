import {useMemo, useState} from 'react';
import type {DecisionMemory} from '../types/decision';

type DecisionsPageProps = {
  memories: DecisionMemory[];
  loading: boolean;
  onOpenSourceMeeting: (meetingId: string) => void;
};

type StatusFilter = 'all' | DecisionMemory['status'];

function displayTitle(memory: DecisionMemory): string {
  return memory.title?.replace(/^历史会议决策[｜|]\s*/, '') || memory.decision;
}

function formatDate(value?: string): string {
  if (!value) return '时间未知';
  return new Intl.DateTimeFormat('zh-CN', {year: 'numeric', month: 'short', day: 'numeric'}).format(new Date(value));
}

const statusLabel: Record<DecisionMemory['status'], string> = {active: 'Active', superseded: 'Superseded', revoked: 'Revoked'};

export function DecisionsPage({memories, loading, onOpenSourceMeeting}: DecisionsPageProps) {
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState<StatusFilter>('all');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const filtered = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase();
    return memories.filter(memory => (status === 'all' || memory.status === status) && (!normalized || [memory.title, memory.decision, memory.subject].some(value => value?.toLocaleLowerCase().includes(normalized))));
  }, [memories, query, status]);
  const selected = filtered.find(memory => memory.id === selectedId) || filtered[0] || null;

  return <section className="decisions-page">
    <header className="decisions-heading"><div><span className="eyebrow">Decision Memory</span><h1>决策记录</h1><p>查看工作空间中经过确认、可追溯的历史决策。</p></div><div className="decision-count"><strong>{memories.filter(item => item.status === 'active').length}</strong><small>Active memories</small></div></header>
    <div className="decision-controls"><input type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="搜索决策内容、主题或来源会议…" aria-label="搜索决策"/><div className="decision-filters">{(['all','active','superseded','revoked'] as StatusFilter[]).map(value => <button key={value} className={status === value ? 'active' : ''} onClick={() => setStatus(value)}>{value === 'all' ? 'All' : statusLabel[value]}</button>)}</div></div>
    <div className="decisions-layout">
      <div className="decision-memory-list">{loading ? <p className="home-muted">正在加载决策记忆…</p> : filtered.length ? filtered.map(memory => <button key={memory.id} className={selected?.id === memory.id ? 'selected' : ''} onClick={() => setSelectedId(memory.id)}><span className={`decision-status ${memory.status}`}>{statusLabel[memory.status]}</span><strong>{memory.decision}</strong><small>{displayTitle(memory)} · {formatDate(memory.effectiveAt || memory.createdAt)}</small></button>) : <div className="decision-empty"><strong>没有匹配的决策</strong><p>{query ? '尝试使用其他关键词或状态筛选。' : '会议中确认的决策会沉淀到这里。'}</p></div>}</div>
      <aside className="decision-memory-detail">{!selected ? <div className="decision-empty"><strong>选择一条决策查看详情</strong></div> : <><div className="decision-detail-heading"><span className={`decision-status ${selected.status}`}>{statusLabel[selected.status]}</span><small>{formatDate(selected.effectiveAt || selected.createdAt)}</small></div><h2>{selected.decision}</h2><dl><div><dt>Source meeting</dt><dd>{displayTitle(selected)}</dd></div><div><dt>Subject</dt><dd>{selected.subject || 'General'}</dd></div><div><dt>Confidence</dt><dd>{Math.round((selected.confidence ?? 1) * 100)}%</dd></div></dl><section className="decision-evidence"><h3>Evidence</h3>{selected.evidence?.length ? selected.evidence.map((evidence,index) => <article key={`${evidence.sourceId || 'evidence'}-${index}`}><span>{evidence.sourceType || 'evidence'}</span><p>{evidence.text || evidence.summary || evidence.title || evidence.sourceId}</p></article>) : <p className="home-muted">当前记录没有可展示的依据摘要。</p>}</section>{selected.supersedesId && <p className="decision-relation">此决策明确替代了更早的决策记忆。</p>}<button className="secondary-button decision-source-button" onClick={() => onOpenSourceMeeting(selected.sourceMeetingId)}>查看来源会议 →</button></>}</aside>
    </div>
  </section>;
}
