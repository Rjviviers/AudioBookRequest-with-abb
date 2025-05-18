from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.services.scraper_service import search_audiobooks, get_audiobook_details
from app.services.qbittorrent_service import qbt_service # Assuming singleton instance
from app.models.audiobook_models import ScrapedSearchResultItem, AudiobookDetail, StatusResponse

router = APIRouter()

@router.get("/search/{query}", response_model=List[ScrapedSearchResultItem])
async def search_for_audiobooks(
    query: str, 
    page: Optional[int] = Query(1, ge=1)
):
    """
    Search AudiobookBay for a given query.
    - **query**: The search term (e.g., "Harry Potter").
    - **page**: Optional page number for search results (default: 1).
    """
    results = await search_audiobooks(query, page=page)
    if not results:
        # You might want to return an empty list or a 404 depending on desired behavior
        # For now, let's return an empty list if scraper itself doesn't raise an error but finds nothing.
        return []
    # Pydantic will validate if the items in results match ScrapedSearchResultItem model
    return results

@router.get("/details", response_model=AudiobookDetail)
async def get_single_audiobook_details(url: str = Query(..., description="The full detail page URL from a search result.")):
    """
    Fetch detailed information for a specific audiobook from its detail page URL.
    This endpoint is expected to return the magnet link.
    - **url**: The full URL to the audiobook's detail page on AudiobookBay.
    """
    if not url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL provided. Must be an absolute HTTP/HTTPS URL.")
    
    details = await get_audiobook_details(url)
    if not details:
        raise HTTPException(status_code=404, detail="Audiobook details not found or could not be scraped from the provided URL.")
    if not details.get("magnet_link"):
        # This case might indicate an issue with scraping the detail page or if the item truly has no magnet
        raise HTTPException(status_code=404, detail="Magnet link not found on the detail page.")
    return details

class DownloadPayload(AudiobookDetail):
    # We expect the client to send us the full AudiobookDetail object, 
    # especially title and magnet_link, which they got from the /details endpoint.
    # No new fields needed, but helps with clarity for the request body.
    pass

@router.post("/download", response_model=StatusResponse)
async def download_audiobook_via_magnet(payload: DownloadPayload):
    """
    Sends a magnet link to qBittorrent for download.
    The payload should be the audiobook detail object obtained from the `/details` endpoint,
    as it contains the necessary `magnet_link` and `title`.
    """
    if not payload.magnet_link:
        raise HTTPException(status_code=400, detail="Magnet link is required in the payload.")
    if not payload.title:
        raise HTTPException(status_code=400, detail="Audiobook title is required in the payload for naming the download folder.")

    if not qbt_service.is_client_available():
        raise HTTPException(status_code=503, detail="qBittorrent service is not available. Check backend logs.")

    result = qbt_service.add_torrent_magnet(magnet_link=payload.magnet_link, audiobook_title=payload.title)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message", "Failed to add torrent to qBittorrent."))
    elif result.get("status") == "warning": # e.g. torrent already exists
        return StatusResponse(status="warning", message=result.get("message"))
        
    return StatusResponse(status="success", message=result.get("message")) 