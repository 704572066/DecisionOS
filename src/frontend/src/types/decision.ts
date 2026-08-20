export type DecisionMemory = {
  id: string; workspaceId?: string; sourceMeetingId: string; sourceSummaryId?: string; sourceDecisionId?: string;
  title?: string; decision: string; subject?: string; status: 'active' | 'superseded' | 'revoked';
  confidence?: number; sourceIds?: string[]; evidence?: unknown[]; effectiveAt?: string; createdAt?: string;
  supersedesId: string | null;
};

export type Reminder = {
  type?: string; title: string; summary: string; suggestion?: string; reason?: string;
  sources?: Array<{type: string; id: string; title?: string; score?: number}>;
  source: {type: string; id: string}; relevanceScore: number; confidence?: number;
};

export type ActiveIntervention = {id: string; title: string; message: string; severity: string; urgency: string; score: number};

export type DecisionCandidate = {
  candidateId: string; projectId: string; meetingId: string; contextId: string;
  title: string; summary: string; statement: string; reasons: string[]; risks: string[];
  evidence: Array<{type: string; id: string; title: string; summary: string; score: number}>;
  suggestedTasks: string[]; status: string;
};

export type DecisionBoard = {
  meetingId: string; projectId: string; contextId: string; objective: string;
  risks: Array<{title: string; summary: string; severity: 'low' | 'medium' | 'high'; sourceIds: string[]}>;
  evidence: Array<{id: string; type: string; title: string; summary: string; score: number}>;
  actions: Array<{text: string; sourceIds: string[]}>;
  currentConditions: Record<string, unknown>;
  recentEvents: Array<{eventId: string; type: string; sourceText: string; field?: string; previousValue?: string | number | null; value?: string | number | null}>;
  resolvedRisks: string[];
  updatedAt: string;
  reasoning?: {
    findings?: Array<{id: string; title: string; summary: string; severity: 'low' | 'medium' | 'high'; status?: string}>;
    interventions?: Array<{id: string; findingId: string; level: 'silent' | 'surface' | 'interrupt'; title: string; message: string; severity: string; urgency: string; score: number}>;
  };
};
