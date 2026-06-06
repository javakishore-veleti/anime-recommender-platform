export interface RecommendationRequest {
  query: string;
}

export interface RecommendationResponse {
  query: string;
  recommendation: string;
  cached: boolean;
}

/** A single parsed recommendation block (derived client-side from the LLM text). */
export interface ParsedRecommendation {
  index: number;
  title: string;
  body: string;
}
