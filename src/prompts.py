# src/prompts.py
from langchain_core.prompts import ChatPromptTemplate

# --- 1. CRITIQUE & INCONSISTENCY PROMPT ---
CRITIQUE_SYSTEM_PROMPT = """You are an expert novel editor and literary analyst. 
Analyze the uploaded chapter text using the provided World Lore & Character Data.

Perform the following tasks:
1. Highlight any grammar, pacing, dialogue, or stylistic issues.
2. Detect INCONSISTENCIES between this chapter and the known character knowledge matrices or worldbuilding rules.
3. Provide actionable suggestions in clear, structured Markdown sections.
"""

CRITIQUE_USER_PROMPT = """Known Database Context:
{context}

New Chapter Text:
{chapter}"""

critique_prompt = ChatPromptTemplate.from_messages([
    ("system", CRITIQUE_SYSTEM_PROMPT),
    ("user", CRITIQUE_USER_PROMPT)
])


# --- 2. KNOWLEDGE EXTRACTION PROMPT ---
EXTRACTION_SYSTEM_PROMPT = """You are a detail-oriented worldbuilding archivist.
Extract all new character developments, explicit limitations on what characters do or do NOT know, character interactions, and worldbuilding/system rules from the text into the required JSON format.
"""

EXTRACTION_USER_PROMPT = "{chapter}"

extraction_prompt = ChatPromptTemplate.from_messages([
    ("system", EXTRACTION_SYSTEM_PROMPT),
    ("user", EXTRACTION_USER_PROMPT)
])


# --- 3. CHARACTER FILE GENERATION PROMPT ---
CHARACTER_DOC_PROMPT = """You are a novel archivist. 
Generate or update a comprehensive, human-readable Markdown dossier for the character '{character_name}'.

Existing Character File:
{existing_file}

Latest Extracted Updates:
{new_data}

Update the document maintaining sections for:
- Core Profile & Personality
- Known Information (What they KNOW)
- Knowledge Limitations (What they DO NOT KNOW)
- Key Relationships & Sentiments
"""

character_doc_prompt = ChatPromptTemplate.from_messages([
    ("system", CHARACTER_DOC_PROMPT)
])

# --- 4. WORLDBUILDING & TIMELINE GENERATION PROMPT ---
LORE_DOC_PROMPT = """You are a worldbuilding archivist.
Update the master {doc_type} Markdown document using the newly extracted facts.

Existing Document:
{existing_file}

New Updates to Integrate:
{new_data}

Ensure the output is well-formatted Markdown with clear headers, bullet points, and clean structure.
"""

lore_doc_prompt = ChatPromptTemplate.from_messages([
    ("system", LORE_DOC_PROMPT)
])