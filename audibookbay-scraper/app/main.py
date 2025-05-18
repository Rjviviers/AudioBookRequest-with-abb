import asyncio
import sys # Import sys to check the platform
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Import CORSMiddleware
from app.api import api_router # Import the main API router

# Set asyncio event loop policy for Windows if applicable
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI(
    title="AudiobookBay Enhanced API",
    version="0.1.0",
    description="API for searching AudiobookBay and managing downloads with qBittorrent."
)

# CORS Middleware Configuration
origins = [
    "http://localhost:3000",  # Allow your Nuxt frontend
    "http://127.0.0.1:3000", # Also allow this common alias for localhost
    # You can add other origins here if needed, e.g., your deployed frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "API is healthy"}

# Placeholder for future routers
# from app.api import search_router, download_router
# app.include_router(search_router.router, prefix="/api")
# app.include_router(download_router.router, prefix="/api")

app.include_router(api_router, prefix="/api") # Include the main API router 