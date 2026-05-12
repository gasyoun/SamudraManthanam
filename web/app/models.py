from pydantic import BaseModel
from typing import List, Optional

class SearchRequest(BaseModel):
    query: str
    mode: str = "plain"  # "plain" | "regex" | "morphological"
    case_sensitive: bool = False
    whole_word: bool = False
    source_ids: Optional[List[int]] = None
    limit: int = 5000

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
