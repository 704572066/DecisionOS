type ManualTranscriptInputProps = {value: string; onChange: (value: string) => void; onSubmit: () => void};

export function ManualTranscriptInput({value, onChange, onSubmit}: ManualTranscriptInputProps) {
  return <details className="manual-fallback"><summary>手工文本调试</summary><textarea rows={3} value={value} onChange={event => onChange(event.target.value)} /><button onClick={onSubmit}>提交并分析</button></details>;
}
