const SESSION_STORAGE_KEY = 'decisionos.currentMeeting.v1';

export type StoredMeetingSession = {meetingId: string; projectId: string};

export function loadMeetingSession(): StoredMeetingSession | null {
  try {
    const raw = localStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<StoredMeetingSession>;
    if (!parsed.meetingId || !parsed.projectId) return null;
    return {meetingId: parsed.meetingId, projectId: parsed.projectId};
  } catch {
    return null;
  }
}

export function saveMeetingSession(session: StoredMeetingSession): void {
  localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
}

export function clearMeetingSession(): void {
  localStorage.removeItem(SESSION_STORAGE_KEY);
}
