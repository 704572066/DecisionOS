import type {RefObject} from 'react';
import {ManualTranscriptInput} from './ManualTranscriptInput';

type TranscriptPanelProps = {
  meetingId: string; recording: boolean; transcript: string; partialTranscript: string;
  manualText: string; scrollRef: RefObject<HTMLDivElement>;
  onStart: () => void; onStop: () => void; onManualTextChange: (value: string) => void; onManualSubmit: () => void;
};

export function TranscriptPanel(props: TranscriptPanelProps) {
  return <section className="transcript-panel realtime-column">
    <div className="panel-title"><h2>实时转写</h2><div>{!props.recording
      ? <button className="record-button" onClick={props.onStart} disabled={!props.meetingId}>● 开始录音</button>
      : <button className="stop-button" onClick={props.onStop}>■ 停止录音</button>}</div></div>
    <div className="transcript transcript-scroll" ref={props.scrollRef}>
      {props.transcript ? props.transcript.split('\n').map((line, index) => <p key={`${line}-${index}`}>{line}</p>) : <p className="placeholder">创建会议并开始讲话，转写文本会显示在这里。</p>}
      {props.partialTranscript && <p className="partial">{props.partialTranscript}</p>}
    </div>
    <ManualTranscriptInput value={props.manualText} onChange={props.onManualTextChange} onSubmit={props.onManualSubmit} />
  </section>;
}
