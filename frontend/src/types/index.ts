// Shared TypeScript types — mirrors backend Pydantic schemas

export interface SearchRequest {
  query: string;
  lat?: number;
  lng?: number;
}

export type AgentName = 'orchestrator' | 'hygiene' | 'location' | 'recommendation';

export type EventType = 'agent_update' | 'result' | 'error';

export interface AgentEvent {
  type: EventType;
  agent?: AgentName;
  message?: string;
  data?: Record<string, unknown>;
}

export interface RankedRecommendation {
  stall_name: string;
  centre_name: string;
  rank: number;
  reasoning: string;
  hygiene_grade: 'A' | 'B' | 'C' | 'D' | 'UNKNOWN';
  is_michelin: boolean;
  is_halal: boolean;
  is_open: boolean;
  distance_km: number;
  google_rating?: number;
  standout_quote?: string | null;
  score?: number;
  lat?: number;
  lng?: number;
}

export interface SearchResult {
  recommendations: RankedRecommendation[];
}
