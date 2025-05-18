from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Any

class ScrapedSearchResultItem(BaseModel):
    title: str
    author: str
    detail_page_url: HttpUrl # Validate that it's a URL
    cover_url: Optional[HttpUrl] = None
    language: Optional[str] = None
    raw_direct_download_link: Optional[HttpUrl] = None # From initial scrape

class AudiobookDetail(BaseModel):
    title: str
    author: Optional[str] = "N/A"
    narrator: Optional[str] = "N/A"
    description: Optional[str] = "N/A"
    language: Optional[str] = None
    magnet_link: Optional[str] = None # This is the key item
    cover_url: Optional[HttpUrl] = None
    detail_page_url: HttpUrl
    info_hash: Optional[str] = None
    trackers: Optional[List[str]] = []

class StatusResponse(BaseModel):
    status: str
    message: Optional[str] = None
    details: Optional[Any] = None 