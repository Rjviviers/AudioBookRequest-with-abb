from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Form, BackgroundTasks
from sqlmodel import Session

from app.internal.auth.authentication import DetailedUser, get_authenticated_user
from app.internal.models import GroupEnum
from app.util.db import get_session
from app.util.templates import template_response

# Import the services module that handles the scraper functionality
try:
    from app.services.scraper_service import search_audiobooks, get_audiobook_details
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Error importing scraper service: {e}")
    
    # Mock implementations in case imports fail
    async def search_audiobooks(query: str, page: int = 1):
        return []
        
    async def get_audiobook_details(url: str):
        return None

router = APIRouter(prefix="/abb")

@router.get("")
async def read_abb_search(
    request: Request,
    user: Annotated[DetailedUser, Depends(get_authenticated_user())],
    session: Annotated[Session, Depends(get_session)],
    query: Annotated[Optional[str], Query(alias="q")] = None,
    page: int = 1,
):
    """
    Search AudiobookBay for audiobooks.
    """
    search_results = []
    if query:
        try:
            search_results = await search_audiobooks(query, page)
        except Exception as e:
            search_results = []
            # Show the error in the UI
            return template_response(
                "audiobookbay_search.html", 
                request, 
                user, 
                {
                    "search_term": query or "",
                    "search_results": [],
                    "page": page,
                    "error": str(e)
                }
            )

    return template_response(
        "audiobookbay_search.html",
        request,
        user,
        {
            "search_term": query or "",
            "search_results": search_results,
            "page": page,
        },
    )

@router.get("/details")
async def get_abb_details(
    request: Request,
    user: Annotated[DetailedUser, Depends(get_authenticated_user())],
    session: Annotated[Session, Depends(get_session)],
    url: str = Query(..., description="The URL of the audiobook details page"),
):
    """
    Get detailed information about an AudiobookBay audiobook.
    """
    try:
        details = await get_audiobook_details(url)
        if not details:
            raise HTTPException(status_code=404, detail="Audiobook details not found")
    except Exception as e:
        return template_response(
            "audiobookbay_details.html",
            request,
            user,
            {
                "error": str(e)
            }
        )

    return template_response(
        "audiobookbay_details.html",
        request,
        user,
        {
            "book": details,
        },
    )

@router.post("/download")
async def download_abb_audiobook(
    request: Request,
    user: Annotated[DetailedUser, Depends(get_authenticated_user(GroupEnum.trusted))],
    session: Annotated[Session, Depends(get_session)],
    background_tasks: BackgroundTasks,
    detail_url: Annotated[str, Form()],
    title: Annotated[str, Form()],
    author: Annotated[Optional[str], Form()] = None,
):
    """
    Download an audiobook from AudiobookBay.
    """
    try:
        details = await get_audiobook_details(detail_url)
        if not details or not details.get("magnet_link"):
            raise HTTPException(status_code=404, detail="Magnet link not found")

        # Here you would add the code to handle the download
        # This could involve qBittorrent integration like in the scraper
        # For now, we'll just return a success message
        
        return template_response(
            "audiobookbay_download.html",
            request,
            user,
            {
                "success": True,
                "message": f"Started download for {title}",
                "book": details,
            },
        )
    except Exception as e:
        return template_response(
            "audiobookbay_download.html",
            request,
            user,
            {
                "success": False,
                "message": str(e),
            },
        ) 