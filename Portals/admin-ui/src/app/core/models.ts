export interface IngestionJob {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | string;
  source: string;
  rows_processed: number;
  error?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface CatalogItem {
  id: number;
  mal_id?: number | null;
  name: string;
  score?: number | null;
  genres?: string | null;
  synopsis?: string | null;
}

export interface CatalogPage {
  items: CatalogItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface ServiceHealth {
  name: string;
  url: string;
  up: boolean;
}
