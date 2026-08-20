import os
import json
import sqlite3
from datetime import datetime
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from config import Config
from src.database import (
    CharacterUpdate, CharacterInteraction, 
    WorldLoreUpdate, ChapterExtraction, init_db
)
from src.prompts import critique_prompt, extraction_prompt
from src.document_generator import update_character_docs, update_worldbuilding_and_timeline

# Initialize DBs & Services
init_db()
embeddings = OpenAIEmbeddings()
vector_db = Chroma(persist_directory=str(Config.CHROMA_DIR), embedding_function=embeddings)
llm = ChatOpenAI(model=Config.LLM_MODEL, temperature=Config.LLM_TEMPERATURE)

def extract_character_names(chapter_text: str) -> list[str]:
    """Helper to fetch existing character names mentioned in chapter text."""
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM characters")
    all_names = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Simple keyword match against DB character roster
    return [name for name in all_names if name.lower() in chapter_text.lower()]

def retrieve_existing_context(query_text: str, chapter_id: str = "0") -> str:
    """Fetch relevant historical text and character details."""
    docs = vector_db.similarity_search(query_text, k=Config.VECTOR_K)
    vector_context = "\n---\n".join([f"Snippet: {d.page_content}" for d in docs])
    
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()
    
    mentioned_chars = extract_character_names(query_text)
    if mentioned_chars:
        placeholders = ','.join('?' for _ in mentioned_chars)
        cursor.execute(f"SELECT name, data FROM characters WHERE name IN ({placeholders})", mentioned_chars)
    else:
        cursor.execute("SELECT name, data FROM characters LIMIT ?", (Config.MAX_CHARACTERS_RETURNED,))
        
    chars = cursor.fetchall()
    conn.close()
    
    return f"Known Characters: {json.dumps(chars)}\n\nPast Chapter Snippets:\n{vector_context}"

def process_chapter(chapter_text: str, chapter_id: str = "1", is_draft: bool = False) -> str:
    """Process chapter for critique and optional knowledge base sync."""
    print("1. Fetching Context...")
    context = retrieve_existing_context(chapter_text, chapter_id)

    print("2. Generating Analysis...")
    critique_chain = critique_prompt | llm
    critique_result = critique_chain.invoke({"context": context, "chapter": chapter_text}).content
    
    if not is_draft:
        print("3. Finalizing Chapter: Extracting Facts and Updating Lore...")
        try:
            structured_llm = llm.with_structured_output(ChapterExtraction)
            extraction_chain = extraction_prompt | structured_llm
            extracted_data: ChapterExtraction = extraction_chain.invoke({"chapter": chapter_text})
            
            _save_extractions_to_db(extracted_data, chapter_id)
            update_character_docs(extracted_data)
            update_worldbuilding_and_timeline(extracted_data)
        except Exception as e:
            print(f"❌ Extraction/Update failed: {e}")
            
        try:
            vector_db.add_texts(
                [chapter_text],
                metadatas=[{"chapter_id": chapter_id, "timestamp": datetime.now().isoformat()}]
            )
        except Exception as e:
            print(f"❌ Vector update failed: {e}")
            
    return critique_result

def _save_extractions_to_db(data: ChapterExtraction, chapter_id: str):
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()
    
    for char in data.character_updates:
        cursor.execute(
            """INSERT INTO characters (name, data, last_updated) 
               VALUES (?, ?, datetime('now')) 
               ON CONFLICT(name) DO UPDATE SET data=excluded.data, last_updated=datetime('now')""",
            (char.name, char.model_dump_json())
        )
    
    for lore in data.world_lore:
        cursor.execute(
            """INSERT INTO lore (topic, rules, last_updated) 
               VALUES (?, ?, datetime('now')) 
               ON CONFLICT(topic) DO UPDATE SET rules=excluded.rules, last_updated=datetime('now')""",
            (lore.topic, json.dumps(lore.rules_or_facts))
        )
    
    for inter in data.interactions:
        cursor.execute(
            """INSERT INTO interactions (char_a, char_b, summary, sentiment, chapter_id) 
               VALUES (?, ?, ?, ?, ?)""",
            (inter.character_a, inter.character_b, inter.summary, inter.sentiment_shift, chapter_id)
        )
        
    conn.commit()
    conn.close()