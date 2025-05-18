FROM node:23-alpine3.20

WORKDIR /app

# Install daisyui
COPY package.json package.json
COPY package-lock.json package-lock.json
RUN npm install

# Setup python
FROM python:3.12-alpine AS linux-amd64
WORKDIR /app
RUN apk add --no-cache curl gcompat build-base
RUN curl https://github.com/tailwindlabs/tailwindcss/releases/download/v4.0.6/tailwindcss-linux-x64-musl -L -o /bin/tailwindcss

FROM python:3.12-alpine AS linux-arm64
WORKDIR /app
RUN apk add --no-cache curl gcompat build-base
RUN curl https://github.com/tailwindlabs/tailwindcss/releases/download/v4.0.6/tailwindcss-linux-arm64-musl -L -o /bin/tailwindcss

FROM ${TARGETOS}-${TARGETARCH}${TARGETVARIANT}
RUN chmod +x /bin/tailwindcss

COPY --from=0 /app/node_modules/ node_modules/
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY uv.lock pyproject.toml /app/
RUN uv sync --frozen --no-cache

# Install AudiobookBay scraper dependencies
COPY audibookbay-scraper/requirements.txt /app/audibookbay-scraper-requirements.txt
RUN uv pip install -r /app/audibookbay-scraper-requirements.txt

COPY alembic/ alembic/
COPY alembic.ini alembic.ini
COPY static/ static/
COPY templates/ templates/
COPY app/ app/

# Copy the AudiobookBay scraper code
COPY audibookbay-scraper/ /app/audibookbay-scraper/

# Create services directory if it doesn't exist
RUN mkdir -p /app/app/services
# Create __init__.py in services directory
RUN echo '"""Services package for AudioBookRequest application."""' > /app/app/services/__init__.py

# Create a simplified scraper service module that uses the local scraper
RUN echo '"""This module provides a wrapper for the audiobookbay scraper."""\n\
import os\n\
import sys\n\
import logging\n\
from typing import Dict, List, Optional, Any\n\
\n\
# Configure logging\n\
logging.basicConfig(level=logging.INFO)\n\
logger = logging.getLogger(__name__)\n\
\n\
# Add the scraper directory to the path\n\
scraper_path = os.path.join("/app", "audibookbay-scraper")\n\
sys.path.append(scraper_path)\n\
\n\
# Set up qBittorrent configuration for the scraper\n\
os.environ.setdefault("QBITTORRENT_HOST", "qbittorrent")\n\
os.environ.setdefault("QBITTORRENT_PORT", "8080")\n\
os.environ.setdefault("QBITTORRENT_USERNAME", "admin")\n\
os.environ.setdefault("QBITTORRENT_PASSWORD", "adminadmin")\n\
os.environ.setdefault("QBITTORRENT_DOWNLOAD_PATH", "/downloads")\n\
\n\
# Import the functions from the scraper\n\
try:\n\
    # Try direct import first\n\
    try:\n\
        from audibookbay_scraper.app.services.scraper_service import search_audiobooks, get_audiobook_details\n\
        logger.info("Successfully imported scraper functions via direct import")\n\
    except ImportError:\n\
        # Try import from the local path as fallback\n\
        sys.path.insert(0, os.path.join(scraper_path, "app"))\n\
        from services.scraper_service import search_audiobooks, get_audiobook_details\n\
        logger.info("Successfully imported scraper functions via local path")\n\
except ImportError as e:\n\
    logger.warning(f"Could not import from AudiobookBay scraper: {e}, using mock implementations")\n\
    \n\
    # Mock implementations\n\
    async def search_audiobooks(query: str, page: int = 1) -> List[Dict[str, Any]]:\n\
        """Search for audiobooks."""\n\
        logger.info(f"Mock search for {query} on page {page}")\n\
        return [\n\
            {\n\
                "title": f"Mock Book for \'{query}\'",\n\
                "author": "Mock Author",\n\
                "detail_page_url": "https://example.com/mock",\n\
                "cover_url": None,\n\
                "language": "English"\n\
            }\n\
        ]\n\
        \n\
    async def get_audiobook_details(url: str) -> Optional[Dict[str, Any]]:\n\
        """Get audiobook details."""\n\
        logger.info(f"Mock details for {url}")\n\
        return {\n\
            "title": "Mock Book Details",\n\
            "author": "Mock Author",\n\
            "narrator": "Mock Narrator",\n\
            "description": "This is a mock book description for testing.",\n\
            "language": "English",\n\
            "magnet_link": "magnet:?xt=urn:btih:mock",\n\
            "cover_url": None,\n\
            "detail_page_url": url\n\
        }\n' > /app/app/services/scraper_service.py

RUN /bin/tailwindcss -i static/tw.css -o static/globals.css -m
# Fetch all the required js files
RUN uv run python /app/app/util/fetch_js.py

ENV ABR_APP__PORT=8000
ARG VERSION
ENV ABR_APP__VERSION=$VERSION

# Enable AudiobookBay router in main.py
RUN sed -i 's/# from app.routers import audiobookbay/from app.routers import audiobookbay/g' /app/app/main.py && \
    sed -i 's/# app.include_router(audiobookbay.router)/app.include_router(audiobookbay.router)/g' /app/app/main.py

CMD /app/.venv/bin/alembic upgrade heads && /app/.venv/bin/fastapi run --port $ABR_APP__PORT

