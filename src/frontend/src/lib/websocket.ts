const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || '';

export function buildWsUrl(path: string): string {
  if (WS_BASE_URL) return `${WS_BASE_URL.replace(/\/$/, '')}${path}`;
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}${path}`;
}
