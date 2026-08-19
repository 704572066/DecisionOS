import React, {useEffect, useMemo, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';

const API = import.meta.env.VITE_API_BASE_URL || '';
const WS_BASE = import.meta.env.VITE_WS_BASE_URL || '';
const SESSION_STORAGE_KEY = 'decisionos.currentMeeting.v1';

type Identity = {user:{id:string;email:string;username:string;status:string};workspace:{id:string;name:string}};
type KnowledgeSource = {
  id:string; projectId:string|null; objectType:'policy'|'decision'|'document'|'evidence';
  name:string; filename:string; mediaType:string; sizeBytes:number;
  status:'uploaded'|'processing'|'ready'|'failed'; summary:string; errorMessage:string;
  itemCount:number; createdAt:string; updatedAt:string;
  items?:Array<{id:string;title:string;content:string}>;
};
type MeetingHistoryItem={id:string;title:string;status:'ended'|'finalized';startedAt:string;endedAt:string|null;finalizedAt:string|null};
type MeetingHistoryDetail={meeting:MeetingHistoryItem;snapshot:null|{
  objective:string;transcript:string;findings:Array<{title:string;summary:string}>;
  recommendations:Array<{title?:string;summary?:string;action?:string}>;
  evidence:Array<{id:string;type:string;title:string;summary:string;score:number}>;
  dialogue:Array<{role:string;content:string;createdAt:string}>;
}};
type MeetingSummaryResult={meetingId:string;summary:string;
  keyFacts:Array<{text:string;sourceIds:string[]}>;decisions:Array<{text:string;sourceIds:string[]}>;
  actionItems:Array<{text:string;sourceIds:string[]}>;openIssues:Array<{text:string;sourceIds:string[]}>;
  evidence:Array<{sourceId:string;sourceType:string;text:string}>;generatedAt:string;
  diagnostics:{extractionMode?:string;acceptedCount?:number;rejectedCount?:number};
};
type DecisionMemory={id:string;sourceMeetingId:string;decision:string;status:'active'|'superseded'|'revoked';supersedesId:string|null};
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
type ActiveIntervention = {
  id: string;
  title: string;
  message: string;
  severity: string;
  urgency: string;
  score: number;
};
type DecisionCandidate = {
  candidateId: string; projectId: string; meetingId: string; contextId: string;
  title: string; summary: string; statement: string; reasons: string[]; risks: string[];
  evidence: Array<{type: string; id: string; title: string; summary: string; score: number}>;
  suggestedTasks: string[]; status: string;
};


type DecisionBoard = {
  meetingId: string;
  projectId: string;
  contextId: string;
  objective: string;
  risks: Array<{title:string;summary:string;severity:'low'|'medium'|'high';sourceIds:string[]}>;
  evidence: Array<{id:string;type:string;title:string;summary:string;score:number}>;
  actions: Array<{text:string;sourceIds:string[]}>;
  currentConditions: Record<string, unknown>;
  recentEvents: Array<{
    eventId:string;
    type:string;
    sourceText:string;
    field?:string;
    previousValue?:string|number|null;
    value?:string|number|null;
  }>;
  resolvedRisks: string[];
  updatedAt: string;
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

const knowledgeStatusLabel:Record<KnowledgeSource['status'],string>={uploaded:'已上传',processing:'处理中',ready:'可用',failed:'失败'};
const knowledgeTypeLabel:Record<KnowledgeSource['objectType'],string>={document:'文档',policy:'企业规则',decision:'历史决策',evidence:'证据'};

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
  const [identity,setIdentity]=useState<Identity|null>(null);
  const [authReady,setAuthReady]=useState(false);
  const [authMode,setAuthMode]=useState<'login'|'register'>('login');
  const [authEmail,setAuthEmail]=useState('');
  const [authPassword,setAuthPassword]=useState('');
  const [authUsername,setAuthUsername]=useState('');
  const [authMessage,setAuthMessage]=useState('');
  const [authMessageType,setAuthMessageType]=useState<'info'|'error'>('info');
  const [activeView,setActiveView]=useState<'meeting'|'history'|'knowledge'>('meeting');
  const [knowledgeSources,setKnowledgeSources]=useState<KnowledgeSource[]>([]);
  const [selectedKnowledge,setSelectedKnowledge]=useState<KnowledgeSource|null>(null);
  const [knowledgeType,setKnowledgeType]=useState<KnowledgeSource['objectType']>('document');
  const [knowledgeBusy,setKnowledgeBusy]=useState(false);
  const knowledgeFileRef=useRef<HTMLInputElement|null>(null);
  const [meetingHistory,setMeetingHistory]=useState<MeetingHistoryItem[]>([]);
  const [historyDetail,setHistoryDetail]=useState<MeetingHistoryDetail|null>(null);
  const [meetingSummary,setMeetingSummary]=useState<MeetingSummaryResult|null>(null);
  const [decisionMemories,setDecisionMemories]=useState<DecisionMemory[]>([]);
  const [summaryBusy,setSummaryBusy]=useState(false);
  const [finalizingMeeting,setFinalizingMeeting]=useState(false);
  const storedSession = useMemo(() => loadStoredSession(), []);
  const [projectId, setProjectId] = useState(storedSession?.projectId || '');
  const [meetingId, setMeetingId] = useState(storedSession?.meetingId || '');
  const [finalTranscript, setFinalTranscript] = useState('');
  const [partialTranscript, setPartialTranscript] = useState('');
  const [manualText, setManualText] = useState(
    '客户要求整体价格下降18%，并希望付款周期延长到180天。'
  );
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [decisionBoard, setDecisionBoard] = useState<DecisionBoard | null>(null);
  const [boardLoading, setBoardLoading] = useState(false);
  const [reminderDrawerOpen, setReminderDrawerOpen] = useState(false);
  const [evidenceDrawerOpen, setEvidenceDrawerOpen] = useState(false);
  const [reminderToast, setReminderToast] = useState<Reminder | null>(null);
  const reminderToastTimerRef = useRef<number | null>(null);
  const transcriptScrollRef = useRef<HTMLDivElement | null>(null);
  const reminderScrollRef = useRef<HTMLDivElement | null>(null);
  const [decisionCandidate, setDecisionCandidate] = useState<DecisionCandidate | null>(null);
  const [candidateTitle, setCandidateTitle] = useState('');
  const [candidateStatement, setCandidateStatement] = useState('');
  const [candidateBusy, setCandidateBusy] = useState(false);
  const [streamingTtftMs, setStreamingTtftMs] = useState<number | null>(null);
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
  const workspaceIdRef = useRef('');

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
    const response = await fetch(input, {...init, credentials:'include', cache:'no-store'});
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

  const loadDecisionBoard = async (targetMeetingId: string, silent = true, force = false) => {
    if (!targetMeetingId) return;
    try {
      if (!silent) setBoardLoading(true);
      const board = await fetchJson<DecisionBoard>(`${API}/decision-board/${targetMeetingId}${force ? '/refresh' : ''}`, force ? {method:'POST'} : undefined);
      if (mountedRef.current) setDecisionBoard(board);
    } catch (error) {
      if (!silent) showError(`加载决策看板失败：${getErrorMessage(error)}`);
    } finally {
      if (!silent && mountedRef.current) setBoardLoading(false);
    }
  };

  const showReminderToast = (reminder: Reminder | undefined) => {
    if (!reminder) return;
    if (reminderToastTimerRef.current !== null) {
      window.clearTimeout(reminderToastTimerRef.current);
    }
    setReminderToast(reminder);
    reminderToastTimerRef.current = window.setTimeout(() => {
      setReminderToast(null);
      reminderToastTimerRef.current = null;
    }, 5000);
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
    await loadDecisionBoard(data.id, true);
    showInfo(`已恢复会议：${data.title}`);
  };

  useEffect(() => {
    const node = transcriptScrollRef.current;
    if (node) {
      node.scrollTop = node.scrollHeight;
    }
  }, [finalTranscript, partialTranscript]);

  useEffect(() => {
    mountedRef.current = true;
    const initialize = async () => {
      try {
        const me=await fetchJson<Identity>(`${API}/auth/me`);
        setIdentity(me);
        if (storedSession?.meetingId) {
          await restoreMeeting(storedSession.meetingId);
        }
      } catch (error) {
        localStorage.removeItem(SESSION_STORAGE_KEY);
      } finally {
        setAuthReady(true);
      }
    };
    initialize();

    return () => {
      mountedRef.current = false;
      stopRecording(true);
    };
  }, []);

  useEffect(()=>{
    if(!authReady) return;
    const target=identity?'/':'/login';
    if(window.location.pathname!==target) window.history.replaceState({},'',target);
  },[authReady,identity]);

  const loadKnowledge = async () => {
    const data=await fetchJson<KnowledgeSource[]>(`${API}/knowledge`);
    if(mountedRef.current) setKnowledgeSources(data);
  };

  const openKnowledge = async (sourceId:string) => {
    try{setSelectedKnowledge(await fetchJson<KnowledgeSource>(`${API}/knowledge/${sourceId}`));}
    catch(error){showError(`加载知识详情失败：${getErrorMessage(error)}`);}
  };

  const uploadKnowledge = async () => {
    const file=knowledgeFileRef.current?.files?.[0];
    if(!file) return showError('请选择要上传的知识文件');
    try{
      setKnowledgeBusy(true);
      const form=new FormData();
      form.append('file',file); form.append('objectType',knowledgeType);
      const response=await fetch(`${API}/knowledge`,{method:'POST',body:form,credentials:'include'});
      if(!response.ok) throw new Error(await response.text() || `请求失败：HTTP ${response.status}`);
      if(knowledgeFileRef.current) knowledgeFileRef.current.value='';
      await loadKnowledge(); showInfo('知识已上传，系统正在解析和建立索引。');
    }catch(error){showError(`上传知识失败：${getErrorMessage(error)}`);}
    finally{setKnowledgeBusy(false);}
  };

  const reprocessKnowledge = async (sourceId:string) => {
    try{await fetchJson(`${API}/knowledge/${sourceId}/reprocess`,{method:'POST'}); await loadKnowledge();}
    catch(error){showError(`重新处理失败：${getErrorMessage(error)}`);}
  };

  const deleteKnowledge = async (source:KnowledgeSource) => {
    if(!window.confirm(`确定删除“${source.name}”吗？删除后将立即退出 AI 检索。`)) return;
    try{
      const response=await fetch(`${API}/knowledge/${source.id}`,{method:'DELETE',credentials:'include'});
      if(!response.ok) throw new Error(await response.text() || `请求失败：HTTP ${response.status}`);
      if(selectedKnowledge?.id===source.id) setSelectedKnowledge(null);
      await loadKnowledge(); showInfo('知识已删除。');
    }catch(error){showError(`删除知识失败：${getErrorMessage(error)}`);}
  };

  const loadMeetingHistory=async()=>{
    const requestedWorkspaceId=workspaceIdRef.current;
    const data=await fetchJson<MeetingHistoryItem[]>(`${API}/meeting-history`);
    if(mountedRef.current&&requestedWorkspaceId&&workspaceIdRef.current===requestedWorkspaceId) setMeetingHistory(data);
  };

  const openMeetingHistory=async(id:string)=>{
    const requestedWorkspaceId=workspaceIdRef.current;
    try{
      const data=await fetchJson<MeetingHistoryDetail>(`${API}/meeting-history/${id}`);
      if(mountedRef.current&&requestedWorkspaceId&&workspaceIdRef.current===requestedWorkspaceId) {
        setHistoryDetail(data); setMeetingSummary(null);
        try{
          setMeetingSummary(await fetchJson<MeetingSummaryResult>(`${API}/meeting-history/${id}/summary`));
          setDecisionMemories(await fetchJson<DecisionMemory[]>(`${API}/decision-memories?meetingId=${encodeURIComponent(id)}`));
        }catch{/* summary is optional */}
      }
    }
    catch(error){showError(`加载历史会议失败：${getErrorMessage(error)}`);}
  };

  const generateMeetingSummary=async()=>{
    if(!historyDetail) return;
    try{setSummaryBusy(true);setMeetingSummary(await fetchJson<MeetingSummaryResult>(`${API}/meeting-history/${historyDetail.meeting.id}/summary`,{method:'POST'}));setDecisionMemories(await fetchJson<DecisionMemory[]>(`${API}/decision-memories?meetingId=${encodeURIComponent(historyDetail.meeting.id)}`));showInfo('结构化会议总结已生成，已确认决策已沉淀为长期记忆。');}
    catch(error){showError(`生成会议总结失败：${getErrorMessage(error)}`);}finally{setSummaryBusy(false);}
  };

  const endAndFinalizeMeeting=async()=>{
    if(!meetingId) return;
    try{
      setFinalizingMeeting(true); stopRecording(true);
      await fetchJson(`${API}/meeting-history/${meetingId}/end`,{method:'POST'});
      await fetchJson(`${API}/meeting-history/${meetingId}/finalize`,{method:'POST'});
      localStorage.removeItem(SESSION_STORAGE_KEY);
      setMeetingId(''); setDecisionBoard(null); setFinalTranscript(''); setReminders([]);
      await loadMeetingHistory(); setActiveView('history'); showInfo('会议已结束并固化到历史记录。');
    }catch(error){showError(`结束会议失败：${getErrorMessage(error)}`);}
    finally{setFinalizingMeeting(false);}
  };

  useEffect(()=>{
    if(!identity || activeView!=='knowledge') return;
    loadKnowledge().catch(error=>showError(`加载知识库失败：${getErrorMessage(error)}`));
    const timer=window.setInterval(()=>{
      if(knowledgeSources.some(source=>source.status==='uploaded'||source.status==='processing')) {
        loadKnowledge().catch(()=>undefined);
      }
    },2500);
    return ()=>window.clearInterval(timer);
  },[identity,activeView,knowledgeSources.some(source=>source.status==='uploaded'||source.status==='processing')]);

  useEffect(()=>{
    if(identity&&activeView==='history') loadMeetingHistory().catch(error=>showError(`加载历史会议失败：${getErrorMessage(error)}`));
  },[identity,activeView]);

  useEffect(()=>{
    // Knowledge details are workspace-scoped. Never retain one user's
    // in-memory data when authentication changes to another workspace.
    workspaceIdRef.current=identity?.workspace.id||'';
    setKnowledgeSources([]);
    setSelectedKnowledge(null);
    setMeetingHistory([]);
    setHistoryDetail(null);
    setMeetingSummary(null);
    setDecisionMemories([]);
  },[identity?.workspace.id]);

  const submitAuth=async()=>{
    try{
      const data=await fetchJson<Identity>(`${API}/auth/${authMode}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:authEmail,password:authPassword,username:authUsername})});
      setAuthMessage(''); setIdentity(data); setAuthReady(true); showInfo(`已进入${data.workspace.name}`);
    }catch(error){setAuthMessageType('error');setAuthMessage(getErrorMessage(error));}
  };

  const logout=async()=>{
    stopRecording(true);
    try{await fetch(`${API}/auth/logout`,{method:'POST',credentials:'include'});}finally{
      localStorage.removeItem(SESSION_STORAGE_KEY); setIdentity(null); setProjectId(''); setMeetingId(''); setDecisionBoard(null); setReminders([]); setKnowledgeSources([]); setSelectedKnowledge(null); setMeetingHistory([]); setHistoryDetail(null); setMeetingSummary(null); setDecisionMemories([]); setActiveView('meeting');
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
        body: JSON.stringify({title: '客户商务谈判'}),
      });
      setMeetingId(data.id);
      setFinalTranscript('');
      setPartialTranscript('');
      setReminders([]);
      setDecisionBoard(null);
      persistMeetingSession(data.id, data.projectId);
      await loadDecisionBoard(data.id, true);
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
          if (meetingId) {
            window.setTimeout(() => loadDecisionBoard(meetingId, true), 120);
          }
          break;
        case 'reminder.started':
          setStreamingTtftMs(null);
          setStreamingReminder({
            id: payload.reminderId,
            title: '',
            summary: '',
            suggestion: '',
            reason: '',
          });
          break;
        case 'reminder.ttft':
          setStreamingTtftMs(payload.firstContentMs ?? null);
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
              [...payload.reminders, ...current].slice(0, 5)
            );
            showReminderToast(payload.reminders[0]);
          }
          if (meetingId) loadDecisionBoard(meetingId, true, true);
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
            }).slice(0, 5);
          });
          showInfo(`发现 ${payload.reminders.length} 条历史提醒`);
          break;
        case 'intervention.delivered': {
          const intervention = payload.intervention as ActiveIntervention;
          const reminder: Reminder = {
            type: 'risk',
            title: intervention.title,
            summary: intervention.message,
            suggestion: intervention.message,
            reason: `主动介入 · ${intervention.urgency}`,
            source: {type: 'intervention', id: intervention.id},
            relevanceScore: intervention.score,
          };
          setReminders((current) => [reminder, ...current].slice(0, 5));
          showReminderToast(reminder);
          if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({
              type: 'intervention.acknowledge',
              deliveryId: payload.deliveryId,
            }));
          }
          if (meetingId) loadDecisionBoard(meetingId, true);
          break;
        }
        case 'intervention.acknowledged':
          if (!payload.acknowledged) showError('主动提醒确认失败或已过期');
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

  const createDecisionCandidate = async (reminder: Reminder) => {
    if (!meetingId) return showError('请先创建会议');
    try {
      setCandidateBusy(true);
      const candidate = await fetchJson<DecisionCandidate>(`${API}/decisions/meetings/${meetingId}/candidate`, {
        method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({reminder}),
      });
      setDecisionCandidate(candidate); setCandidateTitle(candidate.title); setCandidateStatement(candidate.statement);
    } catch (error) { showError(`生成决策草案失败：${getErrorMessage(error)}`); }
    finally { setCandidateBusy(false); }
  };

  const confirmDecisionCandidate = async () => {
    if (!decisionCandidate) return;
    try {
      setCandidateBusy(true);
      const result = await fetchJson<{decisionId:string;status:string;knowledgeUpdated:boolean}>(`${API}/decisions/confirm`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({candidate:decisionCandidate,title:candidateTitle,statement:candidateStatement}),
      });
      setDecisionCandidate(null); showInfo(`决策已确认：${result.decisionId}，企业知识已更新`);
    } catch (error) { showError(`确认决策失败：${getErrorMessage(error)}`); }
    finally { setCandidateBusy(false); }
  };

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
      await loadDecisionBoard(meetingId, false, true);
      showInfo(`识别主题：${(data.topics || []).join('、') || '暂无'}`);
    } catch (error) {
      showError(getErrorMessage(error));
    }
  };

  if(!authReady) return <main className="auth-shell"><p>正在加载我的空间…</p></main>;
  if(!identity) return <main className="auth-shell"><section className="auth-card"><span className="eyebrow">Personal Workspace First</span><h1>DecisionOS</h1><p>{authMode==='login'?'登录我的空间':'创建个人空间'}</p>{authMode==='register'&&<input placeholder="称呼" value={authUsername} onChange={e=>setAuthUsername(e.target.value)}/>}<input type="email" placeholder="邮箱" value={authEmail} onChange={e=>setAuthEmail(e.target.value)}/><input type="password" placeholder="密码（至少 8 位）" value={authPassword} onChange={e=>setAuthPassword(e.target.value)}/><button onClick={submitAuth}>{authMode==='login'?'登录':'注册并创建空间'}</button><button className="link-button" onClick={()=>{setAuthMessage('');setAuthMode(authMode==='login'?'register':'login');}}>{authMode==='login'?'没有账号？创建空间':'已有账号？登录'}</button>{authMessage&&<p className={authMessageType}>{authMessage}</p>}</section></main>;

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
        <div><small>{identity.workspace.name}</small><button className="link-button" onClick={logout}>退出</button></div>
      </header>

      <nav className="workspace-nav">
        <button className={activeView==='meeting'?'active':''} onClick={()=>setActiveView('meeting')}>当前会议</button>
        <button className={activeView==='history'?'active':''} onClick={()=>setActiveView('history')}>历史会议</button>
        <button className={activeView==='knowledge'?'active':''} onClick={()=>setActiveView('knowledge')}>知识库</button>
      </nav>

      {activeView==='history' ? (
        <section className="history-page">
          <div className="knowledge-heading"><div><span className="eyebrow">Final Snapshot</span><h2>历史会议</h2><p>这里展示会议结束时被冻结的状态，不会随知识库或模型变化。</p></div></div>
          <div className="knowledge-layout">
            <div className="knowledge-list">
              {meetingHistory.length===0&&<p className="placeholder">还没有已结束的会议。</p>}
              {meetingHistory.map(item=><article className="knowledge-row" key={item.id} onClick={()=>openMeetingHistory(item.id)}>
                <div><span className={`knowledge-status ${item.status==='finalized'?'ready':'processing'}`}>{item.status==='finalized'?'已固化':'待固化'}</span><strong>{item.title}</strong><small>{new Date(item.startedAt).toLocaleString()}</small></div>
              </article>)}
            </div>
            <aside className="knowledge-detail history-detail">
              {!historyDetail?<p className="placeholder">选择一场历史会议查看 Final Snapshot。</p>:<>
                <h3>{historyDetail.meeting.title}</h3>
                {!historyDetail.snapshot?<p>会议已经结束，尚未固化。</p>:<>
                  <strong>会议目标</strong><p>{historyDetail.snapshot.objective||'未识别明确目标'}</p>
                  <strong>最终转写</strong><p className="history-transcript">{historyDetail.snapshot.transcript||'无转写内容'}</p>
                  <strong>最终关注</strong>{historyDetail.snapshot.findings.length===0?<p>无</p>:historyDetail.snapshot.findings.map((item,index)=><p key={index}>{item.title}：{item.summary}</p>)}
                  <strong>决策依据</strong>{historyDetail.snapshot.evidence.length===0?<p>无</p>:historyDetail.snapshot.evidence.map(item=><p key={item.id}>{item.title} · {Math.round(item.score*100)}%</p>)}
                  <strong>对话记录</strong>{historyDetail.snapshot.dialogue.length===0?<p>无</p>:historyDetail.snapshot.dialogue.map((item,index)=><p key={index}><b>{item.role==='user'?'用户':'DecisionOS'}：</b>{item.content}</p>)}
                  <div className="summary-heading"><strong>结构化会议总结</strong>{!meetingSummary&&<button className="secondary-button" onClick={generateMeetingSummary} disabled={summaryBusy}>{summaryBusy?'生成中…':'生成总结'}</button>}</div>
                  {meetingSummary&&<section className="meeting-summary">
                    <p>{meetingSummary.summary}</p>
                    <strong>已确认事实</strong>{meetingSummary.keyFacts.length?<ul>{meetingSummary.keyFacts.map((item,index)=><li key={index}>{item.text}</li>)}</ul>:<p>无</p>}
                    <strong>会议决策</strong>{meetingSummary.decisions.length?<ul>{meetingSummary.decisions.map((item,index)=><li key={index}>{item.text}</li>)}</ul>:<p>本次会议未形成明确决策。</p>}
                    {decisionMemories.length>0&&<p className="memory-confirmed">✓ 已沉淀 {decisionMemories.filter(item=>item.status==='active').length} 条有效决策记忆</p>}
                    <strong>后续行动</strong>{meetingSummary.actionItems.length?<ul>{meetingSummary.actionItems.map((item,index)=><li key={index}>{item.text}</li>)}</ul>:<p>无</p>}
                    <strong>未解决问题</strong>{meetingSummary.openIssues.length?<ul>{meetingSummary.openIssues.map((item,index)=><li key={index}>{item.text}</li>)}</ul>:<p>无</p>}
                    <small>{meetingSummary.diagnostics.extractionMode==='llm'?'AI 提取 + 规则校验':'规则提取'} · {meetingSummary.evidence.length} 条可追溯依据</small>
                  </section>}
                </>}
              </>}
            </aside>
          </div>
        </section>
      ) : activeView==='knowledge' ? (
        <section className="knowledge-page">
          <div className="knowledge-heading"><div><span className="eyebrow">My Workspace</span><h2>知识库</h2><p>上传企业制度、文档、历史决策和证据，DecisionOS 会在会议中主动使用。</p></div></div>
          <div className="knowledge-upload">
            <input ref={knowledgeFileRef} type="file" accept=".pdf,.docx,.txt,.md,.markdown" />
            <select value={knowledgeType} onChange={e=>setKnowledgeType(e.target.value as KnowledgeSource['objectType'])}>
              <option value="document">文档</option><option value="policy">企业规则</option>
              <option value="decision">历史决策</option><option value="evidence">证据</option>
            </select>
            <button onClick={uploadKnowledge} disabled={knowledgeBusy}>{knowledgeBusy?'上传中…':'上传并处理'}</button>
          </div>
          <div className="knowledge-layout">
            <div className="knowledge-list">
              {knowledgeSources.length===0&&<p className="placeholder">还没有知识。上传第一份企业资料后，它会在这里显示。</p>}
              {knowledgeSources.map(source=><article className="knowledge-row" key={source.id} onClick={()=>openKnowledge(source.id)}>
                <div><span className={`knowledge-status ${source.status}`}>{knowledgeStatusLabel[source.status]}</span><strong>{source.name}</strong><small>{knowledgeTypeLabel[source.objectType]} · {source.filename} · {Math.ceil(source.sizeBytes/1024)} KB</small></div>
                <div className="knowledge-actions">
                  {(source.status==='failed'||source.status==='ready')&&<button className="secondary-button" onClick={e=>{e.stopPropagation();reprocessKnowledge(source.id);}}>重新处理</button>}
                  <button className="danger-button" onClick={e=>{e.stopPropagation();deleteKnowledge(source);}}>删除</button>
                </div>
                {source.status==='failed'&&<p className="error-message">{source.errorMessage}</p>}
              </article>)}
            </div>
            <aside className="knowledge-detail">
              {!selectedKnowledge?<p className="placeholder">选择一条知识查看详情。</p>:<>
                <span className={`knowledge-status ${selectedKnowledge.status}`}>{knowledgeStatusLabel[selectedKnowledge.status]}</span>
                <h3>{selectedKnowledge.name}</h3><p>{selectedKnowledge.summary||'尚未生成摘要。'}</p>
                <small>{selectedKnowledge.itemCount} 个知识片段 · 更新于 {new Date(selectedKnowledge.updatedAt).toLocaleString()}</small>
                {selectedKnowledge.items?.map(item=><details key={item.id}><summary>{item.title}</summary><p>{item.content}</p></details>)}
              </>}
            </aside>
          </div>
          <footer className={messageType==='error'?'error-message':''}>{message||'知识准备完成后会自动进入会议检索。'}</footer>
        </section>
      ) : (<>

      <section className="setup">
        <h2>会议准备</h2>
        <div className="toolbar">
          <button
            onClick={createMeeting}
            disabled={recording}
          >
            创建会议
          </button>
          {meetingId&&<button className="danger-button" onClick={endAndFinalizeMeeting} disabled={recording||finalizingMeeting}>{finalizingMeeting?'正在固化…':'结束并归档会议'}</button>}
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
        <section className="transcript-panel realtime-column">
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

          <div className="transcript transcript-scroll" ref={transcriptScrollRef}>
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

        <section className="decision-surface realtime-column">
          <div className="panel-title">
            <div>
              <span className="eyebrow">Decision Board</span>
              <h2>当前决策状态</h2>
            </div>
            <button className="link-button" onClick={() => meetingId && loadDecisionBoard(meetingId, false)} disabled={!meetingId || boardLoading}>
              {boardLoading ? '刷新中…' : '刷新'}
            </button>
          </div>

          {!decisionBoard ? (
            <div className="decision-board-empty">创建会议后，Decision Board 会持续维护当前目标、风险和下一步行动。</div>
          ) : (
            <div className="decision-board-scroll">
              <div className="decision-board-overview">
                <span className="board-label">当前目标</span>
                <strong>{decisionBoard.objective || '尚未识别明确目标'}</strong>
              </div>

              <section className="board-section priority-layer">
                <div className="board-section-title"><strong>🔴 当前关注</strong></div>
                {decisionBoard.risks.slice(0, 2).map((risk) => (
                  <article key={`${risk.title}-${risk.summary}`} className={`board-risk signal-risk severity-${risk.severity}`}>
                    <span className="risk-dot" />
                    <div><strong>{risk.title}</strong><p>{risk.summary}</p></div>
                  </article>
                ))}
              </section>

              <section className="board-section priority-layer">
                <div className="board-section-title"><strong>🟡 下一步行动</strong></div>
                <ol className="board-actions">
                  {decisionBoard.actions.slice(0, 3).map((action) => <li key={action.text}>{action.text}</li>)}
                </ol>
              </section>

              <div className="decision-board-links">
                <button className="secondary-button" onClick={() => setReminderDrawerOpen(true)}>
                  查看提醒 {reminders.length ? `(${reminders.length})` : ''}
                </button>
                <button className="secondary-button" onClick={() => setEvidenceDrawerOpen(true)}>
                  查看依据 ({decisionBoard.evidence.length})
                </button>
              </div>
            </div>
          )}

          {streamingReminder && (
            <div className="board-generating">AI 正在更新判断{streamingTtftMs !== null && <small> · 首字 {Math.round(streamingTtftMs)}ms</small>}</div>
          )}
        </section>
      </div>

      {reminderToast && (
        <button className="reminder-toast" onClick={() => {setReminderToast(null); setReminderDrawerOpen(true);}}>
          <span className={`toast-icon ${reminderToast.type === 'risk' ? 'risk' : ''}`}>{reminderToast.type === 'risk' ? '!' : 'AI'}</span>
          <span><strong>{reminderToast.title}</strong><small>{reminderToast.summary}</small></span>
        </button>
      )}

      {reminderDrawerOpen && (
        <div className="side-drawer-backdrop" onMouseDown={() => setReminderDrawerOpen(false)}>
          <aside className="side-drawer" onMouseDown={(event) => event.stopPropagation()}>
            <div className="drawer-header"><div><span className="eyebrow">AI Reminder</span><h2>最近提醒</h2></div><button className="link-button" onClick={() => setReminderDrawerOpen(false)}>关闭</button></div>
            <div className="drawer-scroll">
              {reminders.length === 0 && <p className="placeholder">当前没有历史提醒。</p>}
              {reminders.map((reminder, index) => (
                <article className="drawer-reminder" key={`${reminder.source.id}-${index}`}>
                  <strong>{reminder.title}</strong>
                  <p>{reminder.summary}</p>
                  {reminder.suggestion && <p><b>建议：</b>{reminder.suggestion}</p>}
                  <button onClick={() => {setReminderDrawerOpen(false); createDecisionCandidate(reminder);}} disabled={candidateBusy}>生成决策</button>
                </article>
              ))}
            </div>
          </aside>
        </div>
      )}

      {evidenceDrawerOpen && decisionBoard && (
        <div className="side-drawer-backdrop" onMouseDown={() => setEvidenceDrawerOpen(false)}>
          <aside className="side-drawer" onMouseDown={(event) => event.stopPropagation()}>
            <div className="drawer-header"><div><span className="eyebrow">Evidence</span><h2>决策依据</h2></div><button className="link-button" onClick={() => setEvidenceDrawerOpen(false)}>关闭</button></div>
            <div className="drawer-scroll">
              {decisionBoard.evidence.map((item) => (
                <article className="evidence-card" key={item.id}>
                  <div className="evidence-meta"><span>{item.type}</span><span>{Math.round(item.score * 100)}%</span></div>
                  <strong>{item.title}</strong><p>{item.summary}</p>
                </article>
              ))}
            </div>
          </aside>
        </div>
      )}

      {decisionCandidate && (
        <div
          className="decision-modal-backdrop"
          role="presentation"
          onMouseDown={() => {
            if (!candidateBusy) setDecisionCandidate(null);
          }}
        >
          <section
            className="decision-candidate-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="decision-candidate-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="panel-title">
              <div>
                <span className="eyebrow">Decision Draft</span>
                <h2 id="decision-candidate-title">决策草案</h2>
              </div>
              <button
                className="link-button"
                onClick={() => setDecisionCandidate(null)}
                disabled={candidateBusy}
              >
                取消
              </button>
            </div>

            <label>
              标题
              <input
                value={candidateTitle}
                onChange={(event) => setCandidateTitle(event.target.value)}
              />
            </label>

            <label>
              决策内容
              <textarea
                rows={4}
                value={candidateStatement}
                onChange={(event) => setCandidateStatement(event.target.value)}
              />
            </label>

            {decisionCandidate.risks.length > 0 && (
              <div className="candidate-block">
                <strong>风险</strong>
                <ul>
                  {decisionCandidate.risks.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="candidate-block">
              <strong>依据</strong>
              <ul>
                {decisionCandidate.evidence.map((item) => (
                  <li key={item.id}>
                    {item.title}
                    <small> · {item.type} · {Math.round(item.score * 100)}%</small>
                  </li>
                ))}
              </ul>
            </div>

            {decisionCandidate.suggestedTasks.length > 0 && (
              <div className="candidate-block">
                <strong>建议后续事项</strong>
                <ul>
                  {decisionCandidate.suggestedTasks.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="candidate-actions">
              <button
                onClick={confirmDecisionCandidate}
                disabled={
                  candidateBusy ||
                  !candidateTitle.trim() ||
                  !candidateStatement.trim()
                }
              >
                {candidateBusy ? '处理中…' : '确认决策'}
              </button>
            </div>
          </section>
        </div>
      )}

      <footer className={messageType === 'error' ? 'error-message' : ''}>
        {message || '创建会议后即可开始实时分析。'}
      </footer>
      </>)}
    </main>
  );
}

createRoot(document.getElementById('root')!).render(
  <React.StrictMode><App /></React.StrictMode>
);

