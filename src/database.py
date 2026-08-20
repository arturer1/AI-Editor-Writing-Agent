import sqlite3
import json
from pydantic import BaseModel, Field
from typing import List, Optional

# --- Pydantic Data Schemas for Extraction ---
class CharacterUpdate(BaseModel):
    name: str = Field(description="Name of the character")
    traits: Optional[List[str]] = Field(description="New physical or personality traits revealed")
    knowledge_gained: Optional[List[str]] = Field(description="Facts this character learned in this chapter")
    knowledge_lacks: Optional[List[str]] = Field(description="Explicit facts this character is UNAWARE of")

class CharacterInteraction(BaseModel):
    character_a: str
    character_b: str
    summary: str = Field(description="What happened between them")
    sentiment_shift: str = Field(description="e.g., Became more hostile, Trusted, Betrayed")

class WorldLoreUpdate(BaseModel):
    topic: str = Field(description="System, Magic, Tech, Faction, or Location name")
    rules_or_facts: List[str] = Field(description="Rules or details added about this system")

class ChapterExtraction(BaseModel):
    character_updates: List[CharacterUpdate]
    interactions: List[CharacterInteraction]
    world_lore: List[WorldLoreUpdate]

# --- Database Initialization ---
# database.py - Enhanced schema
def init_db(db_path="data/world_db.sqlite"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS characters (
            name TEXT PRIMARY KEY,
            data JSON,
            first_appearance TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            chapter_count INTEGER DEFAULT 1
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lore (
            topic TEXT PRIMARY KEY,
            rules JSON,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            char_a TEXT,
            char_b TEXT,
            summary TEXT,
            sentiment TEXT,
            chapter_id TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chapters (
            id TEXT PRIMARY KEY,
            title TEXT,
            summary TEXT,
            word_count INTEGER,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()