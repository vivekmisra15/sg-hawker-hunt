// Shared TypeScript types — mirrors backend Pydantic schemas

export interface SearchRequest {
  query: string;
  lat?: number;
  lng?: number;
}

export interface RankedRecommendation {
  stall_name: string;
  centre_name: string;
  rank: number;
  reasoning: string;
  hygiene_grade: "A" | "B" | "C" | "D";
  is_michelin: boolean;
  is_halal: boolean;
  is_open: boolean;
  distance_km: number;
  google_rating?: number;
}

export interface AgentEvent {
  type: "agent_update" | "result" | "error";
  agent?: "orchestrator" | "hygiene" | "location" | "recommendation";
  message?: string;
  data?: unknown;
  recommendations?: RankedRecommendation[];
}
