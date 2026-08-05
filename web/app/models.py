from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any
from enum import Enum

class SearchMode(str, Enum):
    plain = "plain"
    regex = "regex"
    morphological = "morphological"

class SearchRequest(BaseModel):
    mode: SearchMode = SearchMode.plain
    query: str = Field(..., min_length=1, max_length=1000)
    case_sensitive: bool = False
    whole_word: bool = False
    source_ids: Optional[List[int]] = None
    limit: int = Field(5000, ge=1, le=5000)

    @field_validator('query')
    @classmethod
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('query cannot be empty or just whitespace')
        return v

    @model_validator(mode='after')
    def validate_regex(self):
        if self.mode == SearchMode.regex:
            patterns = [p.strip() for p in self.query.split('\n') if p.strip()]
            for p in patterns:
                try:
                    import re
                    re.compile(p)
                except re.error as e:
                    raise ValueError(f'Invalid regex pattern: {p} ({e})')
        return self

class SearchResultItem(BaseModel):
    # Compatibility (ordinal) identity. Re-assigned on every ingest — kept for
    # the migration span, never the sole basis of a durable reference (B2).
    source_id: int
    source_title: str
    chapter: Optional[str] = ""
    line_num: int
    link_id: Optional[str] = ""
    line_html: str
    line_text: str
    # Canonical identity (H1925 / Lane B). `None` only on a pre-migration
    # corpus.db whose lines have no canonical_id yet, or a source whose slug
    # backfill has not run.
    source_slug: Optional[str] = None
    canonical_id: Optional[str] = None

class SearchResult(BaseModel):
    query: str
    total: int
    elapsed_ms: float
    sources_hit: int
    results: List[SearchResultItem]
    html_fragment: Optional[str] = None
    search_metadata: Optional[Dict[str, Any]] = None
    # Third member of the canonical tuple: which corpus these results name.
    # A reference is only durable together with the version it was taken from.
    corpus_version: Optional[str] = None

class SourceInfo(BaseModel):
    id: int
    filename: str
    title: str
    sort_order: int
    # Stable across re-ingests (derived from filename); None only for a
    # pre-migration corpus.db before the lifespan backfill has run.
    slug: Optional[str] = None
    # Bibliographic fields populated from per-source .meta.json during ingest.
    title_en: Optional[str] = None
    subtitle: Optional[str] = None
    credit: Optional[str] = None
    credit_role: Optional[str] = None
    imprint: Optional[str] = None
    publisher: Optional[str] = None
    year: Optional[int] = None
