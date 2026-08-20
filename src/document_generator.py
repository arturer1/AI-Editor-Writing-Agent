# src/document_generator.py
import os
import re
from langchain_openai import ChatOpenAI
from src.database import ChapterExtraction
from src.prompts import character_doc_prompt, lore_doc_prompt

llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

def _sanitize_filename(name: str) -> str:
    """Helper to convert character names into safe file names."""
    return re.sub(r'[^\w\-]', '_', name.lower())

# document_generator.py - Enhance with conflict detection
def update_character_docs(extracted_data: ChapterExtraction):
    """Generates character files with conflict detection."""
    os.makedirs("lore/characters", exist_ok=True)
    
    for char in extracted_data.character_updates:
        filename = f"lore/characters/{_sanitize_filename(char.name)}.md"
        existing_content = ""
        conflicts = []
        
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                existing_content = f.read()
            # Detect potential conflicts
            if "age:" in existing_content.lower() and char.age:
                conflicts.append("⚠️ **Potential Age Conflict**")
        
        chain = character_doc_prompt | llm
        updated_md = chain.invoke({
            "character_name": char.name,
            "existing_file": existing_content or "No prior record.",
            "new_data": char.model_dump_json(),
            "conflicts": "\n".join(conflicts) if conflicts else "None detected"
        })
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(updated_md.content)
        print(f"  └─ Updated character file: {filename}")

def update_worldbuilding_and_timeline(extracted_data: ChapterExtraction):
    """Updates the central worldbuilding.md and timeline.md files."""
    os.makedirs("lore", exist_ok=True)
    
    # Update Worldbuilding
    if extracted_data.world_lore:
        wb_file = "lore/worldbuilding.md"
        existing_wb = open(wb_file, "r", encoding="utf-8").read() if os.path.exists(wb_file) else ""
        
        chain = lore_doc_prompt | llm
        updated_wb = chain.invoke({
            "doc_type": "Worldbuilding Overview",
            "existing_file": existing_wb or "No prior worldbuilding recorded.",
            "new_data": [l.model_dump_json() for l in extracted_data.world_lore]
        })
        
        with open(wb_file, "w", encoding="utf-8") as f:
            f.write(updated_wb.content)
        print("  └─ Updated lore/worldbuilding.md")

    # Update Timeline / Interactions
    if extracted_data.interactions:
        timeline_file = "lore/timeline.md"
        existing_tl = open(timeline_file, "r", encoding="utf-8").read() if os.path.exists(timeline_file) else ""
        
        chain = lore_doc_prompt | llm
        updated_tl = chain.invoke({
            "doc_type": "Story Timeline and Interactions",
            "existing_file": existing_tl or "No prior timeline recorded.",
            "new_data": [i.model_dump_json() for i in extracted_data.interactions]
        })
        
        with open(timeline_file, "w", encoding="utf-8") as f:
            f.write(updated_tl.content)
        print("  └─ Updated lore/timeline.md")