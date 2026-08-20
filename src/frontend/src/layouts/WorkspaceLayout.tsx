import type {ReactNode} from 'react';
import type {Identity} from '../types/auth';

export type WorkspaceView = 'home' | 'meetings' | 'meeting' | 'history' | 'meeting-detail' | 'knowledge' | 'decisions' | 'settings';

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
  const meetingsActive = activeView === 'meetings' || activeView === 'meeting' || activeView === 'history' || activeView === 'meeting-detail';
  return <div className="workspace-shell">
    <aside className="workspace-sidebar">
      <button className="workspace-brand" onClick={() => onViewChange('home')} aria-label="返回首页"><span className="workspace-brand-mark">D</span><strong>DecisionOS</strong></button>
      <nav className="workspace-navigation" aria-label="工作空间导航">
        <button className={activeView === 'home' ? 'active' : ''} onClick={() => onViewChange('home')}><span>⌂</span>Home</button>
        <button className={meetingsActive ? 'active' : ''} onClick={() => onViewChange('meetings')}><span>◉</span>Meetings</button>
        {meetingsActive && <div className="workspace-subnav"><button className={activeView === 'meetings' ? 'active' : ''} onClick={() => onViewChange('meetings')}>Overview</button><button className={activeView === 'meeting' ? 'active' : ''} onClick={() => onViewChange('meeting')}>Current meeting</button><button className={activeView === 'history' || activeView === 'meeting-detail' ? 'active' : ''} onClick={() => onViewChange('history')}>History</button></div>}
        <button className={activeView === 'knowledge' ? 'active' : ''} onClick={() => onViewChange('knowledge')}><span>▤</span>Knowledge</button>
        <button className={activeView === 'decisions' ? 'active' : ''} onClick={() => onViewChange('decisions')}><span>◇</span>Decisions</button>
        <button className={activeView === 'settings' ? 'active' : ''} onClick={() => onViewChange('settings')}><span>⚙</span>Settings</button>
      </nav>
      <div className="workspace-sidebar-footer"><div className="workspace-avatar">{(identity.user.username || identity.user.email).slice(0, 1).toUpperCase()}</div><div><strong>{identity.user.username || identity.user.email}</strong><small>{identity.workspace.name}</small></div><button className="workspace-logout" onClick={onLogout} title="退出登录">退出</button></div>
    </aside>
    <div className="workspace-main">
      <header className="workspace-topbar"><div><span className="workspace-mobile-brand">DecisionOS</span></div><div className={`status ${recording ? 'recording' : ''}`}><span />{status}</div></header>
      <main className="workspace-content">{children}</main>
    </div>
  </div>;
}
