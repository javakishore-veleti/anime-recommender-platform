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
  title: string;
  score?: number | null;
  genres?: string | null;
  year?: number | null;
  studio?: string | null;
  status?: string | null;
}

export interface AnimeDetail {
  id: number;
  title: string;
  synopsis?: string | null;
  genres?: string | null;
  score?: number | null;
  year?: number | null;
  episodes?: number | null;
  studio?: string | null;
  status?: string | null;
}

export interface CatalogPage {
  items: CatalogItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface IngestionBatch {
  concept: string;
  batch_index: number;
  rows: number;
  status: string;
}

export interface ServiceHealth {
  name: string;
  url: string;
  up: boolean;
}
