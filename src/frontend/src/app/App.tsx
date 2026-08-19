import React, {useEffect, useMemo, useRef, useState} from 'react';
import '../styles/global.css';
import type {Identity} from '../types/auth';
import type {ActiveIntervention, DecisionBoard, DecisionCandidate, DecisionMemory, Reminder} from '../types/decision';
import type {KnowledgeSource} from '../types/knowledge';
import type {MeetingDetails, MeetingHistoryDetail, MeetingHistoryItem, MeetingSummaryResult} from '../types/meeting';
import type {SpeechRecognitionLike} from '../types/realtime';
import {API_BASE_URL as API, fetchJson} from '../lib/api';
import {getErrorMessage} from '../lib/errors';
import {clearMeetingSession, loadMeetingSession, saveMeetingSession} from '../lib/meetingSession';
import {buildWsUrl} from '../lib/websocket';
import {WorkspaceLayout} from '../layouts/WorkspaceLayout';
import {LoginPage} from '../pages/LoginPage';
import {MeetingSetup} from '../components/meeting/MeetingSetup';
import {TranscriptPanel} from '../components/meeting/TranscriptPanel';
import {DecisionBoard as DecisionBoardView} from '../components/decision/DecisionBoard';
import {KnowledgePage} from '../pages/KnowledgePage';
import {MeetingHistoryPage} from '../pages/MeetingHistoryPage';

export default function App() {
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
  const storedSession = useMemo(() => loadMeetingSession(), []);
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

  const persistMeetingSession = (nextMeetingId: string, nextProjectId: string) => {
    saveMeetingSession({meetingId: nextMeetingId, projectId: nextProjectId});
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
        clearMeetingSession();
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
      clearMeetingSession();
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
      clearMeetingSession(); setIdentity(null); setProjectId(''); setMeetingId(''); setDecisionBoard(null); setReminders([]); setKnowledgeSources([]); setSelectedKnowledge(null); setMeetingHistory([]); setHistoryDetail(null); setMeetingSummary(null); setDecisionMemories([]); setActiveView('meeting');
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

  if(!identity) return <LoginPage ready={authReady} mode={authMode} email={authEmail} password={authPassword} username={authUsername} message={authMessage} messageType={authMessageType} onEmailChange={setAuthEmail} onPasswordChange={setAuthPassword} onUsernameChange={setAuthUsername} onModeChange={(mode)=>{setAuthMessage('');setAuthMode(mode);}} onSubmit={submitAuth} />;

  return (
    <WorkspaceLayout identity={identity} activeView={activeView} recording={recording} connectionState={connectionState} onViewChange={setActiveView} onLogout={logout}>

      {activeView==='history' ? <MeetingHistoryPage items={meetingHistory} detail={historyDetail} summary={meetingSummary} memories={decisionMemories} summaryBusy={summaryBusy} onOpen={openMeetingHistory} onGenerateSummary={generateMeetingSummary} /> : activeView==='knowledge' ? <KnowledgePage sources={knowledgeSources} selected={selectedKnowledge} type={knowledgeType} busy={knowledgeBusy} fileRef={knowledgeFileRef} message={message} messageType={messageType} onTypeChange={setKnowledgeType} onUpload={uploadKnowledge} onOpen={openKnowledge} onReprocess={reprocessKnowledge} onDelete={deleteKnowledge} /> : <>

      <MeetingSetup meetingId={meetingId} recording={recording} finalizing={finalizingMeeting} asrMode={asrMode} browserSpeechSupported={browserSpeechSupported} connectionState={connectionState} onCreate={createMeeting} onFinalize={endAndFinalizeMeeting} onAsrModeChange={setAsrMode} onReconnect={startRecording} onRestore={() => restoreMeeting(meetingId).catch(error => showError(getErrorMessage(error)))} />

      <div className="meeting-grid">
        <TranscriptPanel meetingId={meetingId} recording={recording} transcript={finalTranscript} partialTranscript={partialTranscript} manualText={manualText} scrollRef={transcriptScrollRef} onStart={startRecording} onStop={stopRecording} onManualTextChange={setManualText} onManualSubmit={submitManualText} />

        <DecisionBoardView board={decisionBoard} loading={boardLoading} meetingId={meetingId} reminderCount={reminders.length} streaming={Boolean(streamingReminder)} streamingTtftMs={streamingTtftMs} onRefresh={() => meetingId && loadDecisionBoard(meetingId, false)} onOpenReminders={() => setReminderDrawerOpen(true)} onOpenEvidence={() => setEvidenceDrawerOpen(true)} />
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
      </>}
    </WorkspaceLayout>
  );
}

