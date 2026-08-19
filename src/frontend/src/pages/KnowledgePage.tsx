import type {RefObject} from 'react';
import type {KnowledgeSource} from '../types/knowledge';

const statusLabel: Record<KnowledgeSource['status'], string> = {uploaded: '已上传', processing: '处理中', ready: '可用', failed: '失败'};
const typeLabel: Record<KnowledgeSource['objectType'], string> = {document: '文档', policy: '企业规则', decision: '历史决策', evidence: '证据'};

type KnowledgePageProps = {
  sources: KnowledgeSource[]; selected: KnowledgeSource | null; type: KnowledgeSource['objectType']; busy: boolean;
  fileRef: RefObject<HTMLInputElement>; message: string; messageType: 'info' | 'error';
  onTypeChange: (type: KnowledgeSource['objectType']) => void; onUpload: () => void; onOpen: (id: string) => void;
  onReprocess: (id: string) => void; onDelete: (source: KnowledgeSource) => void;
};

export function KnowledgePage(props: KnowledgePageProps) {
  return <section className="knowledge-page">
    <div className="knowledge-heading"><div><span className="eyebrow">My Workspace</span><h2>知识库</h2><p>上传企业制度、文档、历史决策和证据，DecisionOS 会在会议中主动使用。</p></div></div>
    <div className="knowledge-upload"><input ref={props.fileRef} type="file" accept=".pdf,.docx,.txt,.md,.markdown" /><select value={props.type} onChange={event => props.onTypeChange(event.target.value as KnowledgeSource['objectType'])}><option value="document">文档</option><option value="policy">企业规则</option><option value="decision">历史决策</option><option value="evidence">证据</option></select><button onClick={props.onUpload} disabled={props.busy}>{props.busy ? '上传中…' : '上传并处理'}</button></div>
    <div className="knowledge-layout">
      <div className="knowledge-list">
        {props.sources.length === 0 && <p className="placeholder">还没有知识。上传第一份企业资料后，它会在这里显示。</p>}
        {props.sources.map(source => <article className="knowledge-row" key={source.id} onClick={() => props.onOpen(source.id)}><div><span className={`knowledge-status ${source.status}`}>{statusLabel[source.status]}</span><strong>{source.name}</strong><small>{typeLabel[source.objectType]} · {source.filename} · {Math.ceil(source.sizeBytes / 1024)} KB</small></div><div className="knowledge-actions">{(source.status === 'failed' || source.status === 'ready') && <button className="secondary-button" onClick={event => {event.stopPropagation(); props.onReprocess(source.id);}}>重新处理</button>}<button className="danger-button" onClick={event => {event.stopPropagation(); props.onDelete(source);}}>删除</button></div>{source.status === 'failed' && <p className="error-message">{source.errorMessage}</p>}</article>)}
      </div>
      <aside className="knowledge-detail">{!props.selected ? <p className="placeholder">选择一条知识查看详情。</p> : <><span className={`knowledge-status ${props.selected.status}`}>{statusLabel[props.selected.status]}</span><h3>{props.selected.name}</h3><p>{props.selected.summary || '尚未生成摘要。'}</p><small>{props.selected.itemCount} 个知识片段 · 更新于 {new Date(props.selected.updatedAt).toLocaleString()}</small>{props.selected.items?.map(item => <details key={item.id}><summary>{item.title}</summary><p>{item.content}</p></details>)}</>}</aside>
    </div>
    <footer className={props.messageType === 'error' ? 'error-message' : ''}>{props.message || '知识准备完成后会自动进入会议检索。'}</footer>
  </section>;
}
