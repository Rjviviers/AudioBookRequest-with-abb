"""This module provides a wrapper for the audiobookbay scraper."""
import os
import sys
import logging
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the scraper directory to the path
scraper_path = os.path.join("/app", "audibookbay-scraper")
sys.path.append(scraper_path)

# Set up qBittorrent configuration for the scraper
os.environ.setdefault("QBITTORRENT_HOST", "qbittorrent")
os.environ.setdefault("QBITTORRENT_PORT", "8080")
os.environ.setdefault("QBITTORRENT_USERNAME", "admin")
os.environ.setdefault("QBITTORRENT_PASSWORD", "adminadmin")
os.environ.setdefault("QBITTORRENT_DOWNLOAD_PATH", "/downloads")

# Import the functions from the scraper
try:
    # Try direct import first
    try:
        from audibookbay_scraper.app.services.scraper_service import search_audiobooks, get_audiobook_details
        logger.info("Successfully imported scraper functions via direct import")
    except ImportError:
        # Try import from the local path as fallback
        sys.path.insert(0, os.path.join(scraper_path, "app"))
        from services.scraper_service import search_audiobooks, get_audiobook_details
        logger.info("Successfully imported scraper functions via local path")
except ImportError as e:
    logger.warning(f"Could not import from AudiobookBay scraper: {e}, using mock implementations")
    
    # Mock implementations
    async def search_audiobooks(query: str, page: int = 1) -> List[Dict[str, Any]]:
        """Search for audiobooks."""
        logger.info(f"Mock search for {query} on page {page}")
        return [
            {
                "title": f"Mock Book for '{query}'",
                "author": "Mock Author",
                "detail_page_url": "https://example.com/mock",
                "cover_url": None,
                "language": "English"
            }
        ]
        
    async def get_audiobook_details(url: str) -> Optional[Dict[str, Any]]:
        """Get audiobook details."""
        logger.info(f"Mock details for {url}")
        return {
            "title": "Mock Book Details",
            "author": "Mock Author",
            "narrator": "Mock Narrator",
            "description": "This is a mock book description for testing.",
            "language": "English",
            "magnet_link": "magnet:?xt=urn:btih:mock",
            "cover_url": None,
            "detail_page_url": url
        } 