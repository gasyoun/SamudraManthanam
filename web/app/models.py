from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum

class SearchMode(str, Enum):
    plain = "plain"
    regex = "regex"
    morphological = "morphological"

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    mode: SearchMode = SearchMode.plain
    case_sensitive: bool = False
    whole_word: bool = False
    source_ids: Optional[List[int]] = None
    limit: int = Field(5000, ge=1, le=5000)

    @validator('query')
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('query cannot be empty or just whitespace')
        return v

class SearchResultItem(BaseModel):
    source_id: int
    source_title: str
    chapter: Optional[str] = ""
    line_num: int
    link_id: Optional[str] = ""
    line_html: str

class SearchResult(BaseModel):
    query: str
    total: int
    elapsed_ms: float
    sources_hit: int
    results: List[SearchResultItem]
    html_fragment: Optional[str] = None

class SourceInfo(BaseModel):
    id: int
    filename: str
    title: str
    sort_order: int
