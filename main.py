# main.py
from src.agent import process_chapter

if __name__ == "__main__":
    chapter_path = "drafts/chapter_1.txt"
    IS_DRAFT_CHAPTER = False  # Set to True for rough drafts, False for final chapters
    
    with open(chapter_path, "r", encoding="utf-8") as f:
        chapter_content = f.read()
        
    print(f"--- Processing {chapter_path} (Draft Mode: {IS_DRAFT_CHAPTER}) ---")
    critique_report = process_chapter(chapter_content, is_draft=IS_DRAFT_CHAPTER)
    
    print("\n================ EDITORIAL REPORT ================\n")
    print(critique_report)