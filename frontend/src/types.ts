export type UploadResponse = {
  document_ids: string[];
  accepted_files: Array<{
    document_id: string;
    filename: string;
    status: string;
  }>;
  rejected_files: Array<{
    filename: string;
    reason: string;
  }>;
};

export type DocumentSummary = {
  id: string;
  filename: string;
  file_type: string;
  language: string;
  status: string;
  created_at: string;
};

export type AskRequest = {
  question: string;
  document_ids: string[];
  top_k?: number;
};

export type Citation = {
  document_id: string;
  filename: string;
  page: number | null;
  chunk_id: string;
  snippet: string;
};

export type AskResponse = {
  answer: string;
  mode: "grounded_answer" | "no_evidence";
  citations: Citation[];
  confidence: number;
  used_chunks: number;
};

export type HealthResponse = {
  status: string;
  services: Record<string, string>;
};
