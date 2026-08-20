import os
import json
import sqlite3
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from src.database import (
    CharacterUpdate, CharacterInteraction, 
    WorldLoreUpdate, ChapterExtraction, init_db
)

# Initialize DBs
src.database.init_db()
embeddings = OpenAIEmbeddings()
vector_db = Chroma(persist_directory="data/chroma_db", embedding_function=embeddings)
llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

# agent.py - Improved retrieval
def retrieve_existing_context(query_text: str, chapter_id: str) -> str:
    """Fetch relevant historical text with smart filtering."""
    # 1. Query Vector DB with better chunking
    docs = vector_db.similarity_search(query_text, k=5, filter={"chapter_id": {"$lt": chapter_id}})
    vector_context = "\n---\n".join([f"Chapter {d.metadata.get('chapter', 'unknown')}: {d.page_content}" 
                                     for d in docs])
    
    # 2. Only fetch characters mentioned in this chapter
    conn = sqlite3.connect("data/world_db.sqlite")
    cursor = conn.cursor()
    
    # Use a smarter query - get characters actually mentioned
    mentioned_chars = extract_character_names(query_text)  # You'd implement this
    if mentioned_chars:
        placeholders = ','.join(['?'] * len(mentioned_chars))
        cursor.execute(f"SELECT name, data FROM characters WHERE name IN ({placeholders})", mentioned_chars)
    else:
        cursor.execute("SELECT name, data FROM characters LIMIT 10")  # Fallback
    chars = cursor.fetchall()
    conn.close()
    
    sql_context = f"Known Characters: {json.dumps(chars)}"
    return f"{sql_context}\n\nPast Chapter Snippets:\n{vector_context}"

# agent.py - Wrapper with error handling
def process_chapter(chapter_text: str, chapter_id: str = "chapter_1"):
    try:
        print(f"1. Fetching Database Context for {chapter_id}...")
        context = retrieve_existing_context(chapter_text, chapter_id)
    except Exception as e:
        print(f"❌ Context retrieval failed: {e}")
        context = "No context available - error occurred."
    
    try:
        print("2. Analyzing Chapter...")
        critique_result = _run_critique(chapter_text, context)
    except Exception as e:
        print(f"❌ Critique failed: {e}")
        critique_result = "**ERROR**: Critique generation failed. Please check logs."
    
    try:
        print("3. Extracting Lore...")
        extracted = _run_extraction(chapter_text)
        _save_extractions_to_db(extracted, chapter_id)
        
        print("4. Generating Documentation...")
        from src.document_generator import update_character_docs, update_worldbuilding_and_timeline
        update_character_docs(extracted)
        update_worldbuilding_and_timeline(extracted)
    except Exception as e:
        print(f"❌ Extraction/Update failed: {e}")
    
    # Vector embedding with metadata
    try:
        vector_db.add_texts(
            [chapter_text],
            metadatas=[{"chapter_id": chapter_id, "timestamp": datetime.now().isoformat()}]
        )
    except Exception as e:
        print(f"❌ Vector update failed: {e}")
    
    return critique_result

def _save_extractions_to_db(data: ChapterExtraction):
    conn = sqlite3.connect("data/world_db.sqlite")
    cursor = conn.cursor()
    
    for char in data.character_updates:
        cursor.execute(
            "INSERT INTO characters (name, data, last_updated) VALUES (?, ?, datetime('now')) "
            "ON CONFLICT(name) DO UPDATE SET data=excluded.data, last_updated=datetime('now')",
            (char.name, char.model_dump_json())
        )
    
    for lore in data.world_lore:  # FIX: Save world lore!
        cursor.execute(
            "INSERT INTO lore (topic, rules) VALUES (?, ?) "
            "ON CONFLICT(topic) DO UPDATE SET rules=excluded.rules",
            (lore.topic, json.dumps(lore.rules_or_facts))
        )
    
    for inter in data.interactions:
        cursor.execute(
            "INSERT INTO interactions (char_a, char_b, summary, sentiment, chapter) VALUES (?, ?, ?, ?, ?)",
            (inter.character_a, inter.character_b, inter.summary, inter.sentiment_shift, "chapter_1")  # Add chapter ID
        )
    conn.commit()
    conn.close()