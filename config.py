# config.py - Centralize settings
import os
from pathlib import Path

class Config:
    # Paths
    PROJECT_ROOT = Path(__file__).parent
    DATA_DIR = PROJECT_ROOT / "data"
    LORE_DIR = PROJECT_ROOT / "lore"
    CHROMA_DIR = DATA_DIR / "chroma_db"
    DB_PATH = DATA_DIR / "world_db.sqlite"
    
    # LLM Settings
    LLM_MODEL = "gpt-4o"
    LLM_TEMPERATURE = 0.2
    MAX_TOKENS = 4000
    
    # Database
    VECTOR_K = 5
    MAX_CHARACTERS_RETURNED = 10
    
    # Ensure directories exist
    for dir_path in [DATA_DIR, LORE_DIR, CHROMA_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)