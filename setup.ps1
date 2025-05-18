# Setup script for AudiobookBay integration

# Create services directory if it doesn't exist
if (-not (Test-Path "app\services")) {
    Write-Host "Creating app\services directory"
    New-Item -ItemType Directory -Path "app\services" -Force
} else {
    Write-Host "app\services directory already exists"
}

# Create __init__.py in services directory if it doesn't exist
if (-not (Test-Path "app\services\__init__.py")) {
    Write-Host "Creating app\services\__init__.py"
    Set-Content -Path "app\services\__init__.py" -Value '"""Services package for AudioBookRequest app."""'
} else {
    Write-Host "app\services\__init__.py already exists"
}

# Create a simple implementation of scraper_service.py
$scraper_content = @'
"""
This module provides a wrapper for the audiobookbay scraper.
It imports the functions from the audiobookbay scraper and handles any necessary
setup or configuration.
"""
import logging
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock implementations
async def search_audiobooks(query: str, page: int = 1) -> List[Dict[str, Any]]:
    """Search for audiobooks."""
    logger.info(f"Mock search for '{query}' on page {page}")
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
'@

# Write the scraper service implementation
Set-Content -Path "app\services\scraper_service.py" -Value $scraper_content

Write-Host "Setup complete! Now try running: python -m uvicorn app.main:app --reload" 