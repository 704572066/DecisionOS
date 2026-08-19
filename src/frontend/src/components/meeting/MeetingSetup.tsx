type MeetingSetupProps = {
  meetingId: string;
  recording: boolean;
  finalizing: boolean;
  asrMode: 'browser' | 'deepgram';
  browserSpeechSupported: boolean;
  connectionState: string;
  onCreate: () => void;
  onFinalize: () => void;
  onAsrModeChange: (mode: 'browser' | 'deepgram') => void;
  onReconnect: () => void;
  onRestore: () => void;
};

export function MeetingSetup(props: MeetingSetupProps) {
  return <section className="setup">
    <h2>会议准备</h2>
    <div className="toolbar">
      <button onClick={props.onCreate} disabled={props.recording}>创建会议</button>
      {props.meetingId && <button className="danger-button" onClick={props.onFinalize} disabled={props.recording || props.finalizing}>{props.finalizing ? '正在固化…' : '结束并归档会议'}</button>}
    </div>
    <div className="mode-row">
      <label>ASR 模式<select value={props.asrMode} onChange={event => props.onAsrModeChange(event.target.value as 'browser' | 'deepgram')} disabled={props.recording}>
        <option value="browser">浏览器实时识别（无需密钥）</option><option value="deepgram">Deepgram 流式音频</option>
      </select></label>
      {!props.browserSpeechSupported && props.asrMode === 'browser' && <span className="warning">当前浏览器不支持浏览器语音识别</span>}
      {props.connectionState === 'disconnected' && props.meetingId && <button onClick={props.onReconnect}>重新连接</button>}
    </div>
    {props.meetingId && <div className="meeting-session">当前会议：<code>{props.meetingId}</code><button className="link-button" onClick={props.onRestore}>刷新会议内容</button></div>}
  </section>;
}
