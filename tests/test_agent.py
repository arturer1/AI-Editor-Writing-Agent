import os
import shutil
import sqlite3
import sys
from pathlib import Path
import pytest

# Force Python to recognize the project root directory
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import Config
from src.agent import process_chapter
from src.database import init_db

@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Override database and lore directory paths to keep test data isolated."""
    test_db = tmp_path / "test_world.sqlite"
    test_chroma = tmp_path / "test_chroma"
    test_lore = tmp_path / "test_lore"
    
    # Patch Config paths dynamically during testing
    monkeypatch.setattr(Config, "DB_PATH", test_db)
    monkeypatch.setattr(Config, "CHROMA_DIR", test_chroma)
    monkeypatch.setattr(Config, "LORE_DIR", test_lore)
    
    init_db(db_path=test_db)
    yield

def test_full_agent_pipeline():
    ch1_path = Path("tests/sample_chapter_1.txt")
    ch2_path = Path("tests/sample_chapter_2.txt")
    
    assert ch1_path.exists(), "Sample chapter 1 missing!"
    assert ch2_path.exists(), "Sample chapter 2 missing!"
    
    ch1_text = ch1_path.read_text(encoding="utf-8")
    ch2_text = ch2_path.read_text(encoding="utf-8")
    
    # -------------------------------------------------------------
    # TEST 1: Process Chapter 1 (Final Mode - Populate DBs & Lore)
    # -------------------------------------------------------------
    print("\n--- Running Test Phase 1: Processing Chapter 1 ---")
    report_1 = process_chapter(ch1_text, chapter_id="1", is_draft=False)
    
    # Verify SQLite DB
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM characters")
    chars = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    assert any("Eldrin" in c for c in chars), "Eldrin was not extracted to SQLite!"
    
    # Verify Markdown file generation
    eldrin_md = Config.LORE_DIR / "characters" / "eldrin.md"
    world_md = Config.LORE_DIR / "worldbuilding.md"
    
    assert eldrin_md.exists(), "Individual character file eldrin.md was not created!"
    assert world_md.exists(), "Master worldbuilding.md was not created!"
    
    # -------------------------------------------------------------
    # TEST 2: Process Chapter 2 (Draft Mode - Test Inconsistency Detection)
    # -------------------------------------------------------------
    print("\n--- Running Test Phase 2: Processing Chapter 2 (Inconsistency Check) ---")
    report_2 = process_chapter(ch2_text, chapter_id="2", is_draft=True)
    
    # Check if LLM caught the contradictions
    report_lower = report_2.lower()
    
    # The agent should flag at least one of the intentional contradictions:
    # 1. Eldrin's age (35 vs 42)
    # 2. Red mana rule (explodes vs safe)
    # 3. Relationship history (dock incident / distrust vs trusted since last week)
    has_inconsistency_flag = any(
        keyword in report_lower 
        for keyword in ["age", "red mana", "aetherium", "inconsistency", "contradiction", "docks"]
    )
    
    assert has_inconsistency_flag, "Agent failed to flag known lore contradictions in Chapter 2!"
    print("\n✅ All agent integration tests passed successfully!")