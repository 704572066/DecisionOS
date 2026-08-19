export function getErrorMessage(error: unknown): string {
  if (error instanceof DOMException) {
    if (error.name === 'NotAllowedError') return '麦克风权限被拒绝，请在浏览器地址栏左侧允许麦克风访问。';
    if (error.name === 'NotFoundError') return '未检测到可用麦克风。';
    if (error.name === 'NotReadableError') return '麦克风正被其他程序占用。';
  }
  return error instanceof Error ? error.message : String(error);
}
