type LoginPageProps = {
  ready: boolean;
  mode: 'login' | 'register';
  email: string;
  password: string;
  username: string;
  message: string;
  messageType: 'info' | 'error';
  onEmailChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onUsernameChange: (value: string) => void;
  onModeChange: (mode: 'login' | 'register') => void;
  onSubmit: () => void;
};

export function LoginPage(props: LoginPageProps) {
  if (!props.ready) return <main className="auth-shell"><p>正在加载我的空间…</p></main>;
  return <main className="auth-shell"><section className="auth-card">
    <span className="eyebrow">Personal Workspace First</span><h1>DecisionOS</h1>
    <p>{props.mode === 'login' ? '登录我的空间' : '创建个人空间'}</p>
    {props.mode === 'register' && <input placeholder="称呼" value={props.username} onChange={event => props.onUsernameChange(event.target.value)} />}
    <input type="email" placeholder="邮箱" value={props.email} onChange={event => props.onEmailChange(event.target.value)} />
    <input type="password" placeholder="密码（至少 8 位）" value={props.password} onChange={event => props.onPasswordChange(event.target.value)} />
    <button onClick={props.onSubmit}>{props.mode === 'login' ? '登录' : '注册并创建空间'}</button>
    <button className="link-button" onClick={() => props.onModeChange(props.mode === 'login' ? 'register' : 'login')}>
      {props.mode === 'login' ? '没有账号？创建空间' : '已有账号？登录'}
    </button>
    {props.message && <p className={props.messageType}>{props.message}</p>}
  </section></main>;
}
