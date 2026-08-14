from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any
from enum import Enum

from app.services.regex_executor import validate_patterns

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
        """Gate user patterns on the published regex contract (H1926 C1/C3).

        Was a bare `re.compile` whose ValueError echoed the pattern and the
        engine's message ("Invalid regex pattern: {p} ({e})") into a 422 — the
        contract requires an error payload that reveals no internal details.
        It also accepted patterns the executor refuses (over-long, too many),
        so a request could pass validation and then fail deeper in.

        RegexContractError is not a ValueError, so it escapes pydantic
        unwrapped and is rendered by the app-wide handler in main.py — one
        payload shape for every regex entry point.
        """
        if self.mode == SearchMode.regex:
            validate_patterns(self.query.split('\n'), self.case_sensitive)
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

    @field_validator("chapter", mode="before")
    @classmethod
    def chapter_as_str(cls, v):
        # JSONL/SQLite may store a numeric chapter (H2738 articles used int).
        # The public search schema is a string heading; refuse-to-coerce 500s
        # every query that hits such a row.
        if v is None:
            return ""
        return str(v)

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
