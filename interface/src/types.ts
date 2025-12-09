export type Filters = {
  region?: string;
  beneficiario?: string;
  finalidad?: string;
  fechaDesde?: string;
  fechaHasta?: string;
  cuantiaMin?: number;
  cuantiaMax?: number;
};

export type Citation = {
  snippet: string;
  articulo?: string;
  page?: number;
  pdfUrl: string;
};

export type Convocatoria = {
  id: string;
  titulo: string;
  region?: string;
  beneficiario?: string;
  deadline?: string;
  cuantia?: string | number;
  pdfUrl: string;
  sourceUrl?: string;
  relevance?: number;
};

export type AgentResponse = {
  answer: string;
  citations: Citation[];
  convocatorias: Convocatoria[];
  appliedFilters?: Filters;
  trace?: string[];
  error?: AgentError;
  meta?: {
    model?: string;
    latencyMs?: number;
    lastUpdated?: string;
  };
};

export type AgentError = {
  code: string;
  message: string;
  stage?: string;
  retryAfter?: number;
};

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: AgentResponse;
  createdAt: string;
};
