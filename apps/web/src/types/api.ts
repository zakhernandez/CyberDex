// Types matching your FastAPI schemas.
// Keep in sync manually with apps/api/app/schemas.py.

export type WorkKind = "FILM" | "BOOK" | "ANIME";
export type CreatorKind = "PERSON" | "STUDIO";

export interface WorkListItem {
  id: number;
  kind: WorkKind;
  title: string;
  year: number | null;
  cover_url: string | null;
  slug: string;
}

export interface Creator {
  id: number;
  name: string;
  kind: CreatorKind;
  slug: string;
}

export interface WorkCreatorRead {
  creator: Creator;
  role: string;
  credit_order: number | null;
}

export interface ExternalIdRead {
  source: string;
  external_id: string;
  url: string | null;
}

export interface WorkDetail {
  id: number;
  kind: WorkKind;
  title: string;
  original_title: string | null;
  original_language: string | null;
  year: number | null;
  synopsis: string | null;
  cover_url: string | null;
  slug: string;
  film?: { runtime_minutes: number | null; tagline: string | null } | null;
  book?: { page_count: number | null; isbn_13: string | null } | null;
  anime?: {
    episodes: number | null;
    format: string | null;
    source: string | null;
  } | null;
  creators: WorkCreatorRead[];
  external_ids: ExternalIdRead[];
}

export interface WorkListResponse {
  items: WorkListItem[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
}

export interface CatalogStats {
  total_works: number;
  total_creators: number;
  total_ratings: number;
  by_kind: Array<{ kind: WorkKind; count: number }>;
}

export interface Rating {
  id: number;
  work_id: number;
  score: number;
  created_at: string;
  updated_at: string;
}

export interface RatingWithWork {
  id: number;
  score: number;
  created_at: string;
  updated_at: string;
  work: WorkListItem;
}