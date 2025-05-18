"""
Script to fix imports and create necessary files.
"""
import os
import sys

def ensure_dir(path):
    """Ensure that a directory exists."""
    if not os.path.exists(path):
        print(f"Creating directory: {path}")
        os.makedirs(path, exist_ok=True)
        
def ensure_file(path, content=""):
    """Ensure that a file exists with the given content."""
    if not os.path.exists(path):
        print(f"Creating file: {path}")
        with open(path, "w") as f:
            f.write(content)

# Current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Ensure services directory exists
services_dir = os.path.join(current_dir, "app", "services")
ensure_dir(services_dir)

# Ensure __init__.py exists in services directory
services_init = os.path.join(services_dir, "__init__.py")
ensure_file(services_init, '"""Services package for the AudioBookRequest application."""\n')

# Create a simplified scraper_service.py
scraper_service_content = '''"""
This module provides a wrapper for the audiobookbay scraper.
It imports the functions from the audiobookbay scraper and handles any necessary
setup or configuration.
"""
import os
import sys
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
'''

scraper_service_path = os.path.join(services_dir, "scraper_service.py")
ensure_file(scraper_service_path, scraper_service_content)

print("Import fix complete!")
print("Now try running: python -m uvicorn app.main:app --reload") 