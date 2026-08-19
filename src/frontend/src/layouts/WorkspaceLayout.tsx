import type {ReactNode} from 'react';
import type {Identity} from '../types/auth';

export type WorkspaceView = 'meeting' | 'history' | 'knowledge';

type WorkspaceLayoutProps = {
  identity: Identity;
  activeView: WorkspaceView;
  recording: boolean;
  connectionState: 'idle' | 'connecting' | 'connected' | 'disconnected' | 'error';
  onViewChange: (view: WorkspaceView) => void;
  onLogout: () => void;
  children: ReactNode;
};

export function WorkspaceLayout({identity, activeView, recording, connectionState, onViewChange, onLogout, children}: WorkspaceLayoutProps) {
  const status = recording ? '正在录音' : connectionState === 'connecting' ? '正在连接' : connectionState === 'disconnected' ? '连接已断开' : '待机';
  return <main>
    <header className="hero">
      <div><span className="eyebrow">Bug Fix Sprint 1.1</span><h1>DecisionOS 实时会议</h1><p>实时语音转写、企业历史检索与主动提醒。</p></div>
      <div className={`status ${recording ? 'recording' : ''}`}><span />{status}</div>
      <div><small>{identity.workspace.name}</small><button className="link-button" onClick={onLogout}>退出</button></div>
    </header>
    <nav className="workspace-nav">
      <button className={activeView === 'meeting' ? 'active' : ''} onClick={() => onViewChange('meeting')}>当前会议</button>
      <button className={activeView === 'history' ? 'active' : ''} onClick={() => onViewChange('history')}>历史会议</button>
      <button className={activeView === 'knowledge' ? 'active' : ''} onClick={() => onViewChange('knowledge')}>知识库</button>
    </nav>
    {children}
  </main>;
}
