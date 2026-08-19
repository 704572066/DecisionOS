export type MeetingHistoryItem = {
  id: string;
  title: string;
  status: 'ended' | 'finalized';
  startedAt: string;
  endedAt: string | null;
  finalizedAt: string | null;
};

export type MeetingHistoryDetail = {
  meeting: MeetingHistoryItem;
  snapshot: null | {
    objective: string;
    transcript: string;
    findings: Array<{title: string; summary: string}>;
    recommendations: Array<{title?: string; summary?: string; action?: string}>;
    evidence: Array<{id: string; type: string; title: string; summary: string; score: number}>;
    dialogue: Array<{role: string; content: string; createdAt: string}>;
  };
};

export type MeetingSummaryResult = {
  meetingId: string;
  summary: string;
  keyFacts: Array<{text: string; sourceIds: string[]}>;
  decisions: Array<{text: string; sourceIds: string[]}>;
  actionItems: Array<{text: string; sourceIds: string[]}>;
  openIssues: Array<{text: string; sourceIds: string[]}>;
  evidence: Array<{sourceId: string; sourceType: string; text: string}>;
  generatedAt: string;
  diagnostics: {extractionMode?: string; acceptedCount?: number; rejectedCount?: number};
};

export type MeetingDetails = {
  id: string;
  projectId: string;
  title: string;
  status: string;
  transcript: string;
  segments: Array<{id: string; sequence: number; text: string; confidence?: number; provider: string}>;
};
