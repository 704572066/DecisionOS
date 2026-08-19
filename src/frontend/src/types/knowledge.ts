export type KnowledgeSource = {
  id: string;
  projectId: string | null;
  objectType: 'policy' | 'decision' | 'document' | 'evidence';
  name: string;
  filename: string;
  mediaType: string;
  sizeBytes: number;
  status: 'uploaded' | 'processing' | 'ready' | 'failed';
  summary: string;
  errorMessage: string;
  itemCount: number;
  createdAt: string;
  updatedAt: string;
  items?: Array<{id: string; title: string; content: string}>;
};
