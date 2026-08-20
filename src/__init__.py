# src/__init__.py
# Expose core functionality for easier imports in main.py
from .agent import process_chapter
from .database import init_db

__all__ = ["process_chapter", "init_db"]