export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export async function fetchJson<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const response = await fetch(input, {...init, credentials: 'include', cache: 'no-store'});
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `请求失败：HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}
