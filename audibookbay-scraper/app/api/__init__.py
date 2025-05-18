# This file makes 'api' a Python package 

from fastapi import APIRouter

from app.api.endpoints import audiobooks # Assuming your router file is audiobooks.py

api_router = APIRouter()
api_router.include_router(audiobooks.router, prefix="/audiobooks", tags=["audiobooks"])

# You could add other routers here, e.g. for config, status, etc.
# from app.api.endpoints import system
# api_router.include_router(system.router, prefix="/system", tags=["system"]) 