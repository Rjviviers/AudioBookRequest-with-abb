"""
Check if the necessary files and directories exist.
"""
import os
import sys

def create_dir(path):
    """Create a directory if it doesn't exist."""
    if not os.path.exists(path):
        print(f"Creating {path}")
        os.makedirs(path, exist_ok=True)
        return True
    else:
        print(f"{path} already exists")
        return False

def create_file(path, content):
    """Create a file with the given content if it doesn't exist."""
    if not os.path.exists(path):
        print(f"Creating {path}")
        with open(path, "w") as f:
            f.write(content)
        return True
    else:
        print(f"{path} already exists")
        return False

# Create the services directory
services_dir = os.path.join("app", "services")
create_dir(services_dir)

# Create the __init__.py file
init_path = os.path.join(services_dir, "__init__.py")
create_file(init_path, '"""Services package."""\n')

# Create the scraper_service.py file
scraper_path = os.path.join(services_dir, "scraper_service.py")
scraper_content = '''"""
Mock scraper service.
"""
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

async def search_audiobooks(query: str, page: int = 1) -> List[Dict[str, Any]]:
    """Search for audiobooks."""
    logger.info(f"Mock search for {query}")
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
create_file(scraper_path, scraper_content)

# Try to import app.services.scraper_service
try:
    print("Trying to import app.services.scraper_service...")
    import app.services.scraper_service
    print("Import successful!")
except Exception as e:
    print(f"Import failed: {e}")

print("\nSetup check complete!")
print("Try running: python -m uvicorn app.main:app --reload") 