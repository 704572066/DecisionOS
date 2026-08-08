import React, {useEffect, useMemo, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';

const API = import.meta.env.VITE_API_BASE_URL || '';
const WS_BASE = import.meta.env.VITE_WS_BASE_URL || '';
const SESSION_STORAGE_KEY = 'decisionos.currentMeeting.v1';

type Project = {id: string; name: string; businessGoal: string};
type Reminder = {
  type?: string;
  title: string;
  summary: string;
  suggestion?: string;
  reason?: string;
  sources?: Array<{type: string; id: string; title?: string; score?: number}>;
  source: {type: string; id: string};
  relevanceScore: number;
  confidence?: number;
};
type MeetingDetails = {
  id: string;
  projectId: string;
  title: string;
  status: string;
  transcript: string;
  segments: Array<{
    id: string;
    sequence: number;
    text: string;
    confidence?: number;
    provider: string;
  }>;
};
type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  abort?: () => void;
  onresult: ((event: any) => void) | null;
  onerror: ((event: any) => void) | null;
  onend: (() => void) | null;
  onstart?: (() => void) | null;
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

function getErrorMessage(error: unknown): string {
  if (error instanceof DOMException) {
    if (error.name === 'NotAllowedError') {
      return '麦克风权限被拒绝，请在浏览器地址栏左侧允许麦克风访问。';
    }
    if (error.name === 'NotFoundError') {
      return '未检测到可用麦克风。';
    }
    if (error.name === 'NotReadableError') {
      return '麦克风正被其他程序占用。';
    }
  }
  return error instanceof Error ? error.message : String(error);
}

function loadStoredSession(): {meetingId: string; projectId: string} | null {
  try {
    const raw = localStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed.meetingId || !parsed.projectId) return null;
    return parsed;
  } catch {
    return null;
  }
}

function App() {
  const storedSession = useMemo(() => loadStoredSession(), []);
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState(storedSession?.projectId || '');
  const [meetingId, setMeetingId] = useState(storedSession?.meetingId || '');
  const [finalTranscript, setFinalTranscript] = useState('');
  const [partialTranscript, setPartialTranscript] = useState('');
  const [manualText, setManualText] = useState(
    '客户要求整体价格下降18%，并希望付款周期延长到180天。'
  );
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [streamingReminder, setStreamingReminder] = useState<{
    id: string;
    title: string;
    summary: string;
    suggestion: string;
    reason: string;
  } | null>(null);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'info'|'error'>('info');
  const [recording, setRecording] = useState(false);
  const [connectionState, setConnectionState] = useState<
    'idle'|'connecting'|'connected'|'disconnected'|'error'
  >('idle');
  const [asrMode, setAsrMode] = useState<'browser'|'deepgram'>('browser');

  const socketRef = useRef<WebSocket | null>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const shouldRestartRecognitionRef = useRef(false);
  const recognitionStartingRef = useRef(false);
  const recognitionRestartTimerRef = useRef<number | null>(null);
  const heartbeatTimerRef = useRef<number | null>(null);
  const intentionalSocketCloseRef = useRef(false);
  const mountedRef = useRef(true);

  const browserSpeechSupported = useMemo(
    () => Boolean(window.SpeechRecognition || window.webkitSpeechRecognition),
    []
  );

  const showInfo = (text: string) => {
    setMessageType('info');
    setMessage(text);
  };

  const showError = (text: string) => {
    setMessageType('error');
    setMessage(text);
  };

  const fetchJson = async <T,>(
    input: RequestInfo | URL,
    init?: RequestInit,
  ): Promise<T> => {
    const response = await fetch(input, init);
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || `请求失败：HTTP ${response.status}`);
    }
    return response.json() as Promise<T>;
  };

  const persistMeetingSession = (nextMeetingId: string, nextProjectId: string) => {
    localStorage.setItem(
      SESSION_STORAGE_KEY,
      JSON.stringify({meetingId: nextMeetingId, projectId: nextProjectId}),
    );
  };

  const loadProjects = async () => {
    const data = await fetchJson<Project[]>(`${API}/projects`);
    if (!mountedRef.current) return;
    setProjects(data);
    if (data[0]) setProjectId((current) => current || data[0].id);
  };

  const restoreMeeting = async (targetMeetingId: string) => {
    const data = await fetchJson<MeetingDetails>(
      `${API}/meetings/${targetMeetingId}`,
    );
    if (!mountedRef.current) return;
    setMeetingId(data.id);
    setProjectId(data.projectId);
    setFinalTranscript(data.transcript || '');
    setPartialTranscript('');
    persistMeetingSession(data.id, data.projectId);
    showInfo(`已恢复会议：${data.title}`);
  };

  useEffect(() => {
    mountedRef.current = true;
    const initialize = async () => {
      try {
        await loadProjects();
        if (storedSession?.meetingId) {
          await restoreMeeting(storedSession.meetingId);
        }
      } catch (error) {
        localStorage.removeItem(SESSION_STORAGE_KEY);
        showError(`初始化失败：${getErrorMessage(error)}`);
      }
    };
    initialize();

    return () => {
      mountedRef.current = false;
      stopRecording(true);
    };
  }, []);

  const seed = async () => {
    try {
      const data = await fetchJson<{projectId: string; message: string}>(
        `${API}/demo/seed`,
        {method: 'POST'},
      );
      await loadProjects();
      setProjectId(data.projectId);
      showInfo(data.message);
    } catch (error) {
      showError(getErrorMessage(error));
    }
  };

  const createMeeting = async () => {
    try {
      const data = await fetchJson<{
        id: string;
        projectId: string;
        title: string;
        transcript: string;
      }>(`${API}/meetings`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({projectId, title: '客户商务谈判'}),
      });
      setMeetingId(data.id);
      setFinalTranscript('');
      setPartialTranscript('');
      setReminders([]);
      persistMeetingSession(data.id, data.projectId);
      showInfo(`会议已创建：${data.id}`);
    } catch (error) {
      showError(getErrorMessage(error));
    }
  };

  const handleSocketMessage = (event: MessageEvent) => {
    try {
      const payload = JSON.parse(event.data);
      switch (payload.type) {
        case 'asr.ready':
          setConnectionState('connected');
          showInfo(`实时语音已连接：${payload.mode}`);
          break;
        case 'session.pong':
          break;
        case 'transcript.partial':
          setPartialTranscript(payload.text || '');
          break;
        case 'transcript.final':
          setPartialTranscript('');
          break;
        case 'transcript.saved':
          if (payload.replacedSegmentId) {
            restoreMeeting(meetingId).catch((error) =>
              showError(`恢复转写失败：${getErrorMessage(error)}`)
            );
          } else if (payload.created) {
            setFinalTranscript((current) =>
              [current, payload.segment.text].filter(Boolean).join('\n')
            );
          }
          break;
        case 'reminder.started':
          setStreamingReminder({
            id: payload.reminderId,
            title: '',
            summary: '',
            suggestion: '',
            reason: '',
          });
          break;
        case 'reminder.delta':
          setStreamingReminder((current) => {
            if (!current || current.id !== payload.reminderId) return current;
            return {...current, [payload.field]: payload.accumulated};
          });
          break;
        case 'reminder.completed':
          setStreamingReminder(null);
          if (payload.reminders) {
            setReminders((current) =>
              [...payload.reminders, ...current].slice(0, 10)
            );
          }
          break;
        case 'reminder.failed':
          setStreamingReminder(null);
          showError(payload.message || 'AI 提醒生成失败');
          break;
        case 'reminder.batch':
          setReminders((current) => {
            const merged = [...payload.reminders, ...current];
            const seen = new Set<string>();
            return merged.filter((item) => {
              const key = `${item.source.type}:${item.source.id}:${item.title}:${item.summary}`;
              if (seen.has(key)) return false;
              seen.add(key);
              return true;
            }).slice(0, 10);
          });
          showInfo(`发现 ${payload.reminders.length} 条历史提醒`);
          break;
        case 'error':
          setConnectionState('error');
          showError(payload.message || '语音服务发生错误');
          break;
      }
    } catch (error) {
      showError(`无法解析实时消息：${getErrorMessage(error)}`);
    }
  };

  const clearHeartbeat = () => {
    if (heartbeatTimerRef.current !== null) {
      window.clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
  };

  const startHeartbeat = (socket: WebSocket) => {
    clearHeartbeat();
    heartbeatTimerRef.current = window.setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({type: 'session.ping'}));
      }
    }, 20000);
  };

  const openSocket = async (): Promise<WebSocket> => {
    if (!meetingId) throw new Error('请先创建会议');

    const existing = socketRef.current;
    if (
      existing &&
      (existing.readyState === WebSocket.OPEN ||
       existing.readyState === WebSocket.CONNECTING)
    ) {
      return existing;
    }

    setConnectionState('connecting');
    intentionalSocketCloseRef.current = false;
    const socket = new WebSocket(
      buildWsUrl(`/api/meetings/${meetingId}/audio-stream`)
    );
    socket.binaryType = 'arraybuffer';
    socketRef.current = socket;

    await new Promise<void>((resolve, reject) => {
      const timeout = window.setTimeout(() => {
        socket.close();
        reject(new Error('WebSocket 连接超时'));
      }, 10000);

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
    socket.onerror = () => {
      setConnectionState('error');
      showError('实时连接出现异常。');
    };
    socket.onclose = () => {
      clearHeartbeat();
      socketRef.current = null;
      if (intentionalSocketCloseRef.current) {
        setConnectionState('idle');
        return;
      }
      setConnectionState('disconnected');
      setRecording(false);
      shouldRestartRecognitionRef.current = false;
      showError('实时连接已断开。会议内容已保存，可以点击“重新连接”。');
    };
    startHeartbeat(socket);
    return socket;
  };

  const cancelRecognitionRestart = () => {
    if (recognitionRestartTimerRef.current !== null) {
      window.clearTimeout(recognitionRestartTimerRef.current);
      recognitionRestartTimerRef.current = null;
    }
  };

  const safelyStartRecognition = (
    recognition: SpeechRecognitionLike,
    socket: WebSocket,
  ) => {
    if (
      !shouldRestartRecognitionRef.current ||
      socket.readyState !== WebSocket.OPEN ||
      recognitionStartingRef.current
    ) {
      return;
    }

    recognitionStartingRef.current = true;
    try {
      recognition.start();
    } catch {
      recognitionStartingRef.current = false;
      cancelRecognitionRestart();
      recognitionRestartTimerRef.current = window.setTimeout(
        () => safelyStartRecognition(recognition, socket),
        700,
      );
    }
  };

  const startBrowserSpeech = (socket: WebSocket) => {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      throw new Error(
        '当前浏览器不支持 Web Speech API，请使用 Chrome/Edge 或切换 Deepgram 模式'
      );
    }

    const recognition = new Recognition();
    recognition.lang = 'zh-CN';
    recognition.continuous = true;
    recognition.interimResults = true;
    shouldRestartRecognitionRef.current = true;

    recognition.onstart = () => {
      recognitionStartingRef.current = false;
    };
    recognition.onresult = (event: any) => {
      let partial = '';
      for (
        let index = event.resultIndex;
        index < event.results.length;
        index += 1
      ) {
        const result = event.results[index];
        const text = result[0]?.transcript?.trim() || '';
        if (!text) continue;

        if (result.isFinal) {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
              type: 'transcript.final',
              text,
              confidence: result[0]?.confidence,
            }));
          }
        } else {
          partial += text;
        }
      }

      setPartialTranscript(partial);
      if (partial && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
          type: 'transcript.partial',
          text: partial,
        }));
      }
    };
    recognition.onerror = (event: any) => {
      recognitionStartingRef.current = false;
      const errorCode = event.error || 'unknown';
      if (errorCode === 'not-allowed' || errorCode === 'service-not-allowed') {
        shouldRestartRecognitionRef.current = false;
        showError('麦克风或语音识别权限被拒绝，请检查浏览器权限。');
        setRecording(false);
        return;
      }
      if (errorCode === 'audio-capture') {
        shouldRestartRecognitionRef.current = false;
        showError('未检测到麦克风，或麦克风正被其他程序占用。');
        setRecording(false);
        return;
      }
      if (errorCode !== 'no-speech' && errorCode !== 'aborted') {
        showError(`浏览器语音识别错误：${errorCode}`);
      }
    };
    recognition.onend = () => {
      recognitionStartingRef.current = false;
      if (
        !shouldRestartRecognitionRef.current ||
        socket.readyState !== WebSocket.OPEN
      ) {
        return;
      }
      cancelRecognitionRestart();
      recognitionRestartTimerRef.current = window.setTimeout(
        () => safelyStartRecognition(recognition, socket),
        500,
      );
    };

    recognitionRef.current = recognition;
    safelyStartRecognition(recognition, socket);
  };

  const startDeepgramAudio = async (socket: WebSocket) => {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error(
        '浏览器无法访问麦克风，请使用 HTTPS 或配置 Chrome 不安全来源白名单'
      );
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

    const preferredMimeTypes = ['audio/webm;codecs=opus', 'audio/webm'];
    const mimeType =
      preferredMimeTypes.find((type) => MediaRecorder.isTypeSupported(type)) || '';
    const recorder = new MediaRecorder(
      stream,
      mimeType ? {mimeType} : undefined,
    );

    recorder.ondataavailable = async (event) => {
      if (event.data.size === 0 || socket.readyState !== WebSocket.OPEN) return;
      socket.send(await event.data.arrayBuffer());
    };
    recorder.onerror = () => {
      showError('浏览器录音发生错误。');
    };
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
      showError(getErrorMessage(error));
      stopRecording(true);
    }
  };

  function stopRecording(silent = false) {
    shouldRestartRecognitionRef.current = false;
    recognitionStartingRef.current = false;
    cancelRecognitionRestart();

    try {
      recognitionRef.current?.stop();
    } catch {
      try {
        recognitionRef.current?.abort?.();
      } catch {
        // no-op
      }
    }
    recognitionRef.current = null;

    if (
      recorderRef.current &&
      recorderRef.current.state !== 'inactive'
    ) {
      recorderRef.current.stop();
    }
    recorderRef.current = null;

    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;

    clearHeartbeat();
    const socket = socketRef.current;
    intentionalSocketCloseRef.current = true;
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({type: 'session.stop'}));
      socket.close(1000, 'meeting audio stopped');
    } else if (socket?.readyState === WebSocket.CONNECTING) {
      socket.close();
    }
    socketRef.current = null;

    setRecording(false);
    setPartialTranscript('');
    if (!silent) showInfo('录音已停止，会议内容已保存。');
  }

  const submitManualText = async () => {
    if (!meetingId) {
      showError('请先创建会议');
      return;
    }
    try {
      await fetchJson(`${API}/meetings/${meetingId}/transcript`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text: manualText}),
      });
      await restoreMeeting(meetingId);
      const data = await fetchJson<{topics: string[]; reminders: Reminder[]}>(
        `${API}/meetings/${meetingId}/analyze`,
        {method: 'POST'},
      );
      setReminders(data.reminders || []);
      showInfo(`识别主题：${(data.topics || []).join('、') || '暂无'}`);
    } catch (error) {
      showError(getErrorMessage(error));
    }
  };

  return (
    <main>
      <header className="hero">
        <div>
          <span className="eyebrow">Bug Fix Sprint 1.1</span>
          <h1>DecisionOS 实时会议</h1>
          <p>实时语音转写、企业历史检索与主动提醒。</p>
        </div>
        <div className={`status ${recording ? 'recording' : ''}`}>
          <span />
          {recording
            ? '正在录音'
            : connectionState === 'connecting'
              ? '正在连接'
              : connectionState === 'disconnected'
                ? '连接已断开'
                : '待机'}
        </div>
      </header>

      <section className="setup">
        <h2>会议准备</h2>
        <div className="toolbar">
          <button onClick={seed}>导入示例知识</button>
          <select
            value={projectId}
            onChange={(event) => setProjectId(event.target.value)}
          >
            <option value="">选择项目</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
          <button
            onClick={createMeeting}
            disabled={!projectId || recording}
          >
            创建会议
          </button>
        </div>

        <div className="mode-row">
          <label>
            ASR 模式
            <select
              value={asrMode}
              onChange={(event) =>
                setAsrMode(event.target.value as 'browser'|'deepgram')
              }
              disabled={recording}
            >
              <option value="browser">浏览器实时识别（无需密钥）</option>
              <option value="deepgram">Deepgram 流式音频</option>
            </select>
          </label>

          {!browserSpeechSupported && asrMode === 'browser' && (
            <span className="warning">
              当前浏览器不支持浏览器语音识别
            </span>
          )}

          {connectionState === 'disconnected' && meetingId && (
            <button onClick={startRecording}>重新连接</button>
          )}
        </div>

        {meetingId && (
          <div className="meeting-session">
            当前会议：<code>{meetingId}</code>
            <button
              className="link-button"
              onClick={() =>
                restoreMeeting(meetingId).catch((error) =>
                  showError(getErrorMessage(error))
                )
              }
            >
              刷新会议内容
            </button>
          </div>
        )}
      </section>

      <div className="meeting-grid">
        <section className="transcript-panel">
          <div className="panel-title">
            <h2>实时转写</h2>
            <div>
              {!recording ? (
                <button
                  className="record-button"
                  onClick={startRecording}
                  disabled={!meetingId}
                >
                  ● 开始录音
                </button>
              ) : (
                <button
                  className="stop-button"
                  onClick={() => stopRecording()}
                >
                  ■ 停止录音
                </button>
              )}
            </div>
          </div>

          <div className="transcript">
            {finalTranscript
              ? finalTranscript.split('\n').map((line, index) => (
                  <p key={`${line}-${index}`}>{line}</p>
                ))
              : (
                <p className="placeholder">
                  创建会议并开始讲话，转写文本会显示在这里。
                </p>
              )}
            {partialTranscript && (
              <p className="partial">{partialTranscript}</p>
            )}
          </div>

          <details className="manual-fallback">
            <summary>手工文本调试</summary>
            <textarea
              rows={3}
              value={manualText}
              onChange={(event) => setManualText(event.target.value)}
            />
            <button onClick={submitManualText}>提交并分析</button>
          </details>
        </section>

        <section className="reminder-panel">
          <h2>AI 实时提醒</h2>
          {streamingReminder && (
            <article className="streaming-reminder">
              <div className="streaming-state">AI 生成中…</div>
              {streamingReminder.title && <strong>{streamingReminder.title}</strong>}
              {streamingReminder.summary && <p>{streamingReminder.summary}</p>}
              {streamingReminder.suggestion && (
                <p><strong>建议：</strong>{streamingReminder.suggestion}</p>
              )}
              {streamingReminder.reason && (
                <p><strong>依据：</strong>{streamingReminder.reason}</p>
              )}
            </article>
          )}
          {reminders.length === 0 && (
            <div className="empty-reminder">
              当会议出现价格、付款、利润或风险议题时，
              相关历史信息会主动显示。
            </div>
          )}
          {reminders.map((reminder, index) => (
            <article key={`${reminder.source.id}-${index}`}>
              <strong>{reminder.title}</strong>
              <p>{reminder.summary}</p>
              {reminder.suggestion && (
                <p className="reminder-suggestion">
                  <strong>建议：</strong>{reminder.suggestion}
                </p>
              )}
              {reminder.reason && (
                <p className="reminder-reason">
                  <strong>依据：</strong>{reminder.reason}
                </p>
              )}
              <small>
                来源：{reminder.source.type} / {reminder.source.id}
                {' · '}
                相关度 {Math.round(reminder.relevanceScore * 100)}%
              </small>
            </article>
          ))}
        </section>
      </div>

      <footer className={messageType === 'error' ? 'error-message' : ''}>
        {message || '请先导入示例知识并创建会议。'}
      </footer>
    </main>
  );
}

createRoot(document.getElementById('root')!).render(
  <React.StrictMode><App /></React.StrictMode>
);
