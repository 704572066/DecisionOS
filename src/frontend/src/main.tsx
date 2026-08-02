import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
type Project={id:string,name:string,businessGoal:string};
type Reminder={title:string,summary:string,source:{type:string,id:string},relevanceScore:number};

function App(){
 const [projects,setProjects]=useState<Project[]>([]); const [projectId,setProjectId]=useState('');
 const [meetingId,setMeetingId]=useState(''); const [text,setText]=useState('客户要求整体价格下降18%，并希望付款周期延长到90天。');
 const [reminders,setReminders]=useState<Reminder[]>([]); const [message,setMessage]=useState('');
 const [decision,setDecision]=useState('将折扣控制在8%左右，并优先谈判缩短付款周期。');
 const load=async()=>{const r=await fetch(`${API}/projects`); const p=await r.json(); setProjects(p); if(p[0])setProjectId(p[0].id)};
 useEffect(()=>{load()},[]);
 const seed=async()=>{const r=await fetch(`${API}/demo/seed`,{method:'POST'}); const d=await r.json(); setMessage(d.message); await load(); setProjectId(d.projectId)};
 const createMeeting=async()=>{const r=await fetch(`${API}/meetings`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({projectId,title:'客户商务谈判'})}); const d=await r.json(); setMeetingId(d.id); setMessage(`会议已创建：${d.id}`)};
 const analyze=async()=>{if(!meetingId)return setMessage('请先创建会议'); await fetch(`${API}/meetings/${meetingId}/transcript`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})}); const r=await fetch(`${API}/meetings/${meetingId}/analyze`,{method:'POST'}); const d=await r.json(); setReminders(d.reminders); setMessage(`识别主题：${(d.topics||[]).join('、')||'暂无'}`)};
 const save=async()=>{const r=await fetch(`${API}/decisions`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({projectId,meetingId:meetingId||null,title:'客户A价格与付款条件决策',statement:decision,evidenceSummary:reminders.map(x=>x.summary).join('\n'),taskTitle:'准备修订报价方案',taskObjective:'形成折扣与付款周期组合方案',taskOwner:'销售负责人'})}); const d=await r.json(); setMessage(`已保存 Decision ${d.decisionId}，Task ${d.taskId||'未创建'}`)};
 return <main><header><h1>DecisionOS Demo</h1><p>企业历史上下文 · 实时提醒 · 决策沉淀</p></header>
 <section><h2>1. 准备知识</h2><button onClick={seed}>导入示例知识</button><select value={projectId} onChange={e=>setProjectId(e.target.value)}><option value="">选择项目</option>{projects.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select><button onClick={createMeeting} disabled={!projectId}>创建会议</button></section>
 <section><h2>2. 会议输入</h2><textarea rows={6} value={text} onChange={e=>setText(e.target.value)}/><button onClick={analyze}>分析当前内容</button></section>
 <section><h2>3. 实时提醒</h2>{reminders.map((r,i)=><article key={i}><strong>{r.title}</strong><p>{r.summary}</p><small>来源：{r.source.type} / {r.source.id} · 相关度 {Math.round(r.relevanceScore*100)}%</small></article>)}</section>
 <section><h2>4. 确认决策</h2><textarea rows={4} value={decision} onChange={e=>setDecision(e.target.value)}/><button onClick={save} disabled={!projectId}>保存 Decision 与 Task</button></section>
 <footer>{message}</footer></main>
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
