# AudiobookBay Integration

This document explains how the AudiobookBay scraper has been integrated into the AudioBookRequest application.

## Overview

The integration adds the ability to:
1. Search for audiobooks on AudiobookBay
2. View detailed information about audiobooks
3. Download audiobooks using qBittorrent

## Setup

### Development Setup

1. Make sure you have both the main application and the scraper code:
   - Main app: `/app`
   - Scraper: `/audibookbay-scraper`

2. Run the setup script to create the necessary files:
   ```
   python fix_imports.py
   ```

3. Start the application with the integration enabled:
   ```
   python -m uvicorn app.main:app --reload
   ```

### Docker Setup

The integration is included in the Docker setup with the following components:

1. **AudioBookRequest Web App**: Serves the main application and includes the AudiobookBay integration
2. **qBittorrent**: Handles downloading audiobooks
3. **Gotify**: Notification service (optional)

To start the application with Docker:

```
mkdir -p downloads data/qbittorrent/config data/gotify/data
docker-compose --profile local up
```

## Configuration

### qBittorrent Configuration

The qBittorrent service is configured with the following default settings:
- Host: qbittorrent
- Port: 8080
- Username: admin
- Password: adminadmin
- Web UI: http://localhost:8081 (when running with Docker)

### Environment Variables

The configuration can be customized using environment variables in `config/scraper.env`:

```
# AudiobookBay scraper configuration

# AudiobookBay cookie (if needed)
AUDIOBOOK_BAY_COOKIE=

# qBittorrent Configuration
QBITTORRENT_HOST=qbittorrent
QBITTORRENT_PORT=8080
QBITTORRENT_USERNAME=admin
QBITTORRENT_PASSWORD=adminadmin
QBITTORRENT_DOWNLOAD_PATH=/downloads
```

## Directory Structure

- `/app`: Main application code
  - `/app/routers/audiobookbay.py`: Router for AudiobookBay integration
  - `/app/services/scraper_service.py`: Service that interfaces with the scraper
- `/audibookbay-scraper`: AudiobookBay scraper code
- `/templates`: Templates for UI
  - `/templates/audiobookbay_search.html`: Search results page
  - `/templates/audiobookbay_details.html`: Details page
  - `/templates/audiobookbay_download.html`: Download confirmation
- `/downloads`: Directory for downloaded audiobooks
- `/data`: Directory for service data
  - `/data/qbittorrent/config`: qBittorrent configuration
  - `/data/gotify/data`: Gotify data

## Accessing the Integration

Once the application is running, the AudiobookBay search can be accessed through:
- Web UI: Go to http://localhost:8000/abb
- You can also access it via the book icon in the navigation bar

## Troubleshooting

If you encounter issues with the integration:

1. Check the application logs for errors
2. Verify qBittorrent is running and accessible
3. Check that the environment variables are set correctly
4. Ensure the services directory and its files exist in the application

For Docker issues:
1. Check container logs: `docker-compose logs web`
2. Check qBittorrent logs: `docker-compose logs qbittorrent`
3. Verify volumes are mounted correctly 