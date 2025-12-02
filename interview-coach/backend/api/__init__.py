"""
Interview Coach API

FastAPI-based API for the interview coaching system.
"""

from .routes import router
from .websocket import ConnectionManager

__all__ = ["router", "ConnectionManager"]
