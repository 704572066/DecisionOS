import React, {useEffect, useMemo, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';

const API = import.meta.env.VITE_API_BASE_URL || '';
const WS_BASE = import.meta.env.VITE_WS_BASE_URL || '';

type Project = {id: string; name: string; businessGoal: string};
type Reminder = {
  title: string;
  summary: string;
  source: {type: string; id: string};
  relevanceScore: number;
};
type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  onresult: ((event: any) => void) | null;
  onerror: ((event: any) => void) | null;
  onend: (() => void) | null;
};

declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  }
}

function buildWsUrl(path: string): string {
  if (WS_BASE) return `${WS_BASE.replace(/\/$/, '')}${path}`;
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}${path}`;
}

function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState('');
  const [meetingId, setMeetingId] = useState('');
  const [finalTranscript, setFinalTranscript] = useState('');
  const [partialTranscript, setPartialTranscript] = useState('');
  const [manualText, setManualText] = useState('客户要求整体价格下降18%，并希望付款周期延长到180天。');
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [message, setMessage] = useState('');
  const [recording, setRecording] = useState(false);
  const [connectionState, setConnectionState] = useState<'idle'|'connecting'|'connected'|'error'>('idle');
  const [asrMode, setAsrMode] = useState<'browser'|'deepgram'>('browser');

  const socketRef = useRef<WebSocket | null>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const shouldRestartRecognitionRef = useRef(false);

  const browserSpeechSupported = useMemo(
    () => Boolean(window.SpeechRecognition || window.webkitSpeechRecognition),
    []
  );

  const load = async () => {
    const response = await fetch(`${API}/projects`);
    if (!response.ok) throw new Error('项目加载失败');
    const projectsData = await response.json();
    setProjects(projectsData);
    if (projectsData[0]) setProjectId((current: string) => current || projectsData[0].id);
  };

  useEffect(() => {
    load().catch((error) => setMessage(String(error)));
    return () => {
      stopRecording();
    };
  }, []);

  const seed = async () => {
    const response = await fetch(`${API}/demo/seed`, {method: 'POST'});
    const data = await response.json();
    setMessage(data.message);
    await load();
    setProjectId(data.projectId);
  };

  const createMeeting = async () => {
    const response = await fetch(`${API}/meetings`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({projectId, title: '客户商务谈判'}),
    });
    if (!response.ok) throw new Error('会议创建失败');
    const data = await response.json();
    setMeetingId(data.id);
    setFinalTranscript('');
    setPartialTranscript('');
    setReminders([]);
    setMessage(`会议已创建：${data.id}`);
  };

  const handleSocketMessage = (event: MessageEvent) => {
    const payload = JSON.parse(event.data);
    switch (payload.type) {
      case 'asr.ready':
        setConnectionState('connected');
        setMessage(`实时语音已连接：${payload.mode}`);
        break;
      case 'transcript.partial':
        setPartialTranscript(payload.text || '');
        break;
      case 'transcript.final':
        setPartialTranscript('');
        break;
      case 'transcript.saved':
        setFinalTranscript((current) => [current, payload.segment.text].filter(Boolean).join('\n'));
        break;
      case 'reminder.batch':
        setReminders((current) => [...payload.reminders, ...current].slice(0, 10));
        setMessage(`发现 ${payload.reminders.length} 条历史提醒`);
        break;
      case 'error':
        setConnectionState('error');
        setMessage(payload.message || '语音服务发生错误');
        break;
    }
  };

  const openSocket = async (): Promise<WebSocket> => {
    if (!meetingId) throw new Error('请先创建会议');
    setConnectionState('connecting');
    const socket = new WebSocket(buildWsUrl(`/api/meetings/${meetingId}/audio-stream`));
    socket.binaryType = 'arraybuffer';
    socketRef.current = socket;

    await new Promise<void>((resolve, reject) => {
      const timeout = window.setTimeout(() => reject(new Error('WebSocket 连接超时')), 10000);
      socket.onopen = () => {
        window.clearTimeout(timeout);
        socket.send(JSON.stringify({
          mode: asrMode,
          language: 'zh-CN',
          mimeType: 'audio/webm;codecs=opus',
        }));
        resolve();
      };
      socket.onerror = () => {
        window.clearTimeout(timeout);
        reject(new Error('WebSocket 连接失败'));
      };
    });

    socket.onmessage = handleSocketMessage;
    socket.onclose = () => {
      setConnectionState('idle');
      setRecording(false);
    };
    return socket;
  };

  const startBrowserSpeech = (socket: WebSocket) => {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) throw new Error('当前浏览器不支持 Web Speech API，请使用 Chrome/Edge 或切换 Deepgram 模式');

    const recognition = new Recognition();
    recognition.lang = 'zh-CN';
    recognition.continuous = true;
    recognition.interimResults = true;
    shouldRestartRecognitionRef.current = true;

    recognition.onresult = (event: any) => {
      let partial = '';
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const result = event.results[index];
        const text = result[0]?.transcript?.trim() || '';
        if (!text) continue;
        if (result.isFinal) {
          socket.send(JSON.stringify({
            type: 'transcript.final',
            text,
            confidence: result[0]?.confidence,
          }));
        } else {
          partial += text;
        }
      }
      if (partial) {
        setPartialTranscript(partial);
        socket.send(JSON.stringify({type: 'transcript.partial', text: partial}));
      }
    };
    recognition.onerror = (event: any) => {
      setMessage(`浏览器语音识别错误：${event.error || 'unknown'}`);
      if (event.error === 'not-allowed') shouldRestartRecognitionRef.current = false;
    };
    recognition.onend = () => {
      if (shouldRestartRecognitionRef.current && socket.readyState === WebSocket.OPEN) {
        try { recognition.start(); } catch { /* ignore duplicate start */ }
      }
    };
    recognition.start();
    recognitionRef.current = recognition;
  };

  const startDeepgramAudio = async (socket: WebSocket) => {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error('浏览器无法访问麦克风，请确认使用 HTTPS');
    }
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });
    streamRef.current = stream;

    const preferredMimeTypes = [
      'audio/webm;codecs=opus',
      'audio/webm',
    ];
    const mimeType = preferredMimeTypes.find((type) => MediaRecorder.isTypeSupported(type)) || '';
    const recorder = new MediaRecorder(stream, mimeType ? {mimeType} : undefined);
    recorder.ondataavailable = async (event) => {
      if (event.data.size === 0 || socket.readyState !== WebSocket.OPEN) return;
      socket.send(await event.data.arrayBuffer());
    };
    recorder.onerror = (event) => setMessage(`录音错误：${String(event)}`);
    recorder.start(300);
    recorderRef.current = recorder;
  };

  const startRecording = async () => {
    try {
      if (!meetingId) throw new Error('请先创建会议');
      const socket = await openSocket();
      if (asrMode === 'browser') {
        startBrowserSpeech(socket);
      } else {
        await startDeepgramAudio(socket);
      }
      setRecording(true);
    } catch (error) {
      setConnectionState('error');
      setMessage(error instanceof Error ? error.message : String(error));
      stopRecording();
    }
  };

  const stopRecording = () => {
    shouldRestartRecognitionRef.current = false;
    try { recognitionRef.current?.stop(); } catch { /* no-op */ }
    recognitionRef.current = null;

    if (recorderRef.current && recorderRef.current.state !== 'inactive') {
      recorderRef.current.stop();
    }
    recorderRef.current = null;

    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;

    const socket = socketRef.current;
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({type: 'session.stop'}));
      socket.close(1000, 'meeting audio stopped');
    }
    socketRef.current = null;
    setRecording(false);
    setPartialTranscript('');
  };

  const submitManualText = async () => {
    if (!meetingId) return setMessage('请先创建会议');
    const append = await fetch(`${API}/meetings/${meetingId}/transcript`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text: manualText}),
    });
    if (!append.ok) throw new Error('文本保存失败');
    setFinalTranscript((current) => [current, manualText].filter(Boolean).join('\n'));
    const response = await fetch(`${API}/meetings/${meetingId}/analyze`, {method: 'POST'});
    const data = await response.json();
    setReminders(data.reminders || []);
    setMessage(`识别主题：${(data.topics || []).join('、') || '暂无'}`);
  };

  return (
    <main>
      <header className="hero">
        <div>
          <span className="eyebrow">Sprint 1 · Realtime Meeting Intelligence</span>
          <h1>DecisionOS 实时会议</h1>
          <p>实时语音转写、企业历史检索与主动提醒。</p>
        </div>
        <div className={`status ${recording ? 'recording' : ''}`}>
          <span />
          {recording ? '正在录音' : connectionState === 'connecting' ? '正在连接' : '待机'}
        </div>
      </header>

      <section className="setup">
        <h2>会议准备</h2>
        <div className="toolbar">
          <button onClick={seed}>导入示例知识</button>
          <select value={projectId} onChange={(event) => setProjectId(event.target.value)}>
            <option value="">选择项目</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>{project.name}</option>
            ))}
          </select>
          <button onClick={createMeeting} disabled={!projectId || recording}>创建会议</button>
        </div>
        <div className="mode-row">
          <label>
            ASR 模式
            <select
              value={asrMode}
              onChange={(event) => setAsrMode(event.target.value as 'browser'|'deepgram')}
              disabled={recording}
            >
              <option value="browser">浏览器实时识别（无需密钥）</option>
              <option value="deepgram">Deepgram 流式音频</option>
            </select>
          </label>
          {!browserSpeechSupported && asrMode === 'browser' && (
            <span className="warning">当前浏览器不支持浏览器语音识别</span>
          )}
        </div>
      </section>

      <div className="meeting-grid">
        <section className="transcript-panel">
          <div className="panel-title">
            <h2>实时转写</h2>
            <div>
              {!recording ? (
                <button className="record-button" onClick={startRecording} disabled={!meetingId}>
                  ● 开始录音
                </button>
              ) : (
                <button className="stop-button" onClick={stopRecording}>■ 停止录音</button>
              )}
            </div>
          </div>
          <div className="transcript">
            {finalTranscript ? finalTranscript.split('\n').map((line, index) => (
              <p key={`${line}-${index}`}>{line}</p>
            )) : <p className="placeholder">创建会议并开始讲话，转写文本会显示在这里。</p>}
            {partialTranscript && <p className="partial">{partialTranscript}</p>}
          </div>

          <details className="manual-fallback">
            <summary>手工文本调试</summary>
            <textarea rows={3} value={manualText} onChange={(event) => setManualText(event.target.value)} />
            <button onClick={() => submitManualText().catch((error) => setMessage(String(error)))}>
              提交并分析
            </button>
          </details>
        </section>

        <section className="reminder-panel">
          <h2>AI 实时提醒</h2>
          {reminders.length === 0 && (
            <div className="empty-reminder">
              当会议出现价格、付款、利润或风险议题时，相关历史信息会主动显示。
            </div>
          )}
          {reminders.map((reminder, index) => (
            <article key={`${reminder.source.id}-${index}`}>
              <strong>{reminder.title}</strong>
              <p>{reminder.summary}</p>
              <small>
                来源：{reminder.source.type} / {reminder.source.id}
                {' · '}相关度 {Math.round(reminder.relevanceScore * 100)}%
              </small>
            </article>
          ))}
        </section>
      </div>

      <footer>{message || '请先导入示例知识并创建会议。'}</footer>
    </main>
  );
}

createRoot(document.getElementById('root')!).render(
  <React.StrictMode><App /></React.StrictMode>
);
