"""
Smart Legal Document Processor - The "Dual-Brain" Ingestion Engine

This module implements Phase A of the refined Smart Legal RAG System:
1. Structural Segmentation (Atomic Split based on Legal Boundaries)
2. Semantic Enrichment (LLM-based metadata generation)
3. Vector Construction (Rich Chunks with human keywords)
4. Dual Storage (Vector DB + JSON Map)
"""

import re
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.docstore.document import Document

import core


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class SectionCandidate:
    """Represents a parsed legal section/article"""
    section_id: str          # e.g., "304", "103A"
    title: str               # e.g., "Punishment for Murder"
    body: str                # The legal text content
    page: int                # Page number in original document
    act: str                 # e.g., "BNS", "IPC"
    subsections: List[str]   # Sub-clause IDs if split further
    
    
@dataclass
class EnrichedSection:
    """Section with LLM-generated metadata"""
    section_id: str
    title: str
    body: str
    page: int
    act: str
    
    # LLM-generated fields
    common_crime_name: str
    human_keywords: List[str]
    summary: str
    severity: str            # Cognizable/Non-Cognizable/N/A
    bailable: str            # Yes/No/Depends/N/A
    
    # Storage references
    chroma_uuid: Optional[str] = None


# ============================================================================
# STEP 1: STRUCTURAL SEGMENTATION (Atomic Split)
# ============================================================================

def extract_sections_from_text(text: str, filename: str = "", act_name: str = "UNKNOWN") -> List[SectionCandidate]:
    """
    Splits document using Legal Boundaries instead of character counts.
    
    Regex Pattern: Matches "Section 304.", "Article 21", "Sec. 103A", etc.
    Logic:
        - Identify Header (Section ID + Title)
        - Capture Body (Text up to next section)
        - Apply Sub-clause Splitter if section > 6000 chars
    
    Returns: List of SectionCandidate objects
    """
    
    # Primary regex for Section/Article headers
    # Matches: "Section 304.", "Article 21", "Sec 103A", etc.
    section_pattern = re.compile(
        r'(?m)^(?:Section|Article|Sec\.?)\s*(\d+[A-Z]*)\s*\.?\s*[:\-\–]?\s*(.+?)$',
        re.IGNORECASE
    )
    
    candidates = []
    matches = list(section_pattern.finditer(text))
    
    if not matches:
        print(f"No sections found in {filename}. Treating as single document.")
        # Return entire document as one chunk
        return [SectionCandidate(
            section_id="FULL_DOC",
            title=filename,
            body=text[:6000],  # Limit to reasonable size
            page=1,
            act=act_name,
            subsections=[]
        )]
    
    for i, match in enumerate(matches):
        section_id = match.group(1).strip()
        title = match.group(2).strip()
        
        # Extract body: from current match end to next match start (or end of text)
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start_pos:end_pos].strip()
        
        # Estimate page number (rough calculation: 3000 chars per page)
        page = (match.start() // 3000) + 1
        
        # Check if section is too large (> 6000 chars)
        if len(body) > 6000:
            # Apply sub-clause splitter
            subsections = split_into_subclauses(body, section_id)
            
            # Create a candidate for each sub-clause
            for sub_id, sub_body in subsections:
                candidates.append(SectionCandidate(
                    section_id=f"{section_id}_{sub_id}",
                    title=f"{title} - Part {sub_id}",
                    body=sub_body,
                    page=page,
                    act=act_name,
                    subsections=[sub_id]
                ))
        else:
            candidates.append(SectionCandidate(
                section_id=section_id,
                title=title,
                body=body,
                page=page,
                act=act_name,
                subsections=[]
            ))
    
    print(f"✓ Extracted {len(candidates)} sections from {filename}")
    return candidates


def split_into_subclauses(text: str, parent_id: str) -> List[Tuple[str, str]]:
    """
    Secondary splitter for massive sections.
    Splits by sub-clause markers: (1), (2), (a), (b), etc.
    
    Returns: List of (sub_id, text) tuples
    """
    # Match patterns like (1), (2), (a), (b), etc.
    subclause_pattern = re.compile(r'\n\s*\(([0-9a-z]+)\)\s+')
    
    matches = list(subclause_pattern.finditer(text))
    
    if not matches:
        # No sub-clauses found, split by character limit
        chunks = []
        for i in range(0, len(text), 5000):
            chunks.append((f"P{i//5000 + 1}", text[i:i+5000]))
        return chunks
    
    subclauses = []
    for i, match in enumerate(matches):
        sub_id = match.group(1)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sub_text = text[start:end].strip()
        subclauses.append((sub_id, sub_text))
    
    return subclauses


# ============================================================================
# STEP 2: SEMANTIC ENRICHMENT (The "Translator")
# ============================================================================

def enrich_section_with_llm(section: SectionCandidate) -> EnrichedSection:
    """
    Passes section through Qwen to generate metadata.
    
    Generates:
        - common_crime_name: e.g., "Snatching"
        - human_keywords: List of slang terms
        - summary: 1-sentence simple English explanation
        - severity: Cognizable/Non-Cognizable
        - bailable: Yes/No/Depends
    
    Returns: EnrichedSection object
    """
    
    prompt = f"""You are a legal metadata extractor. Analyze this legal provision and return ONLY a valid JSON object.

LEGAL TEXT:
Section {section.section_id}: {section.title}
{section.body[:1500]}

INSTRUCTIONS:
Return a JSON object with these exact keys:
{{
    "type": "PENAL" or "PROCEDURAL",
    "human_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "summary": "One sentence simple English explanation",
    "severity": "Cognizable/Non-Cognizable/N/A",
    "bailable": "Yes/No/Depends/N/A"
}}

EXAMPLES OF GOOD KEYWORDS:
- For theft: ["stealing", "took someone's belongings", "grabbed phone", "property theft", "movable property"]
- For assault: ["hit someone", "physical attack", "beating", "injury", "violence"]

IMPORTANT: 
- Use "PENAL" for sections defining crimes/punishments
- Use "PROCEDURAL" for sections about legal processes, definitions, or administrative matters
- Return ONLY the JSON object. No explanations or extra text.
"""

    try:
        # Use LLM to generate metadata
        response = core.safe_llm_invoke(prompt, max_tokens=300, temperature=0.3)
        
        # Parse JSON response
        # Clean potential markdown code blocks
        response = response.replace("```json", "").replace("```", "").strip()
        
        metadata = json.loads(response)
        
        # Validate required fields
        required = ["type", "human_keywords", "summary", "severity", "bailable"]
        for field in required:
            if field not in metadata:
                raise ValueError(f"Missing field: {field}")
        
        return EnrichedSection(
            section_id=section.section_id,
            title=section.title,
            body=section.body,
            page=section.page,
            act=section.act,
            common_crime_name=metadata.get("type", "PROCEDURAL"),  # Store type as common_crime_name for now
            human_keywords=metadata["human_keywords"][:5],  # Limit to 5
            summary=metadata["summary"],
            severity=metadata["severity"],
            bailable=metadata["bailable"]
        )
        
    except Exception as e:
        print(f"⚠ LLM enrichment failed for Section {section.section_id}: {e}")
        print(f"Response was: {response[:200] if 'response' in locals() else 'No response'}")
        
        # Return minimal enrichment on failure
        return EnrichedSection(
            section_id=section.section_id,
            title=section.title,
            body=section.body,
            page=section.page,
            act=section.act,
            common_crime_name="PROCEDURAL",  # Default type on failure
            human_keywords=[section.title.lower(), section.section_id],
            summary=section.title,
            severity="N/A",
            bailable="N/A"
        )


def enrich_sections_batch(sections: List[SectionCandidate], batch_size: int = 5) -> List[EnrichedSection]:
    """
    FAST BATCH ENRICHMENT - Processes multiple sections in a single LLM call.
    
    This is 5x faster than individual enrichment because:
    - Reduces LLM API overhead
    - Single prompt for multiple sections
    - Parallel JSON parsing
    
    Args:
        sections: List of sections to enrich
        batch_size: Number of sections per batch (default: 5)
    
    Returns:
        List of EnrichedSection objects
    """
    
    enriched_results = []
    
    # Process in batches
    for batch_start in range(0, len(sections), batch_size):
        batch = sections[batch_start:batch_start + batch_size]
        
        # Build batch prompt
        sections_text = ""
        for idx, section in enumerate(batch):
            sections_text += f"""
--- SECTION {idx + 1} ---
ID: {section.section_id}
Title: {section.title}
Content: {section.body[:800]}

"""
        
        prompt = f"""You are a legal metadata extractor. Analyze these {len(batch)} legal provisions and return a JSON ARRAY.

{sections_text}

INSTRUCTIONS:
Return a JSON array with {len(batch)} objects, each with these exact keys:
[
  {{
    "type": "PENAL" or "PROCEDURAL",
    "human_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "summary": "One sentence simple English explanation",
    "severity": "Cognizable/Non-Cognizable/N/A",
    "bailable": "Yes/No/Depends/N/A"
  }}
]

RULES:
- Use "PENAL" for crimes/punishments, "PROCEDURAL" for processes/definitions
- Maintain the same order as the sections above
- Return ONLY the JSON array, no explanations

"""
        
        try:
            # Single LLM call for entire batch
            response = core.safe_llm_invoke(prompt, max_tokens=800, temperature=0.3)
            response = response.replace("```json", "").replace("```", "").strip()
            
            # Parse batch results
            metadata_list = json.loads(response)
            
            # Validate it's a list
            if not isinstance(metadata_list, list):
                raise ValueError("LLM did not return an array")
            
            # Map results back to sections
            for idx, (section, metadata) in enumerate(zip(batch, metadata_list)):
                try:
                    enriched = EnrichedSection(
                        section_id=section.section_id,
                        title=section.title,
                        body=section.body,
                        page=section.page,
                        act=section.act,
                        common_crime_name=metadata.get("type", "PROCEDURAL"),
                        human_keywords=metadata.get("human_keywords", [section.title.lower()])[:5],
                        summary=metadata.get("summary", section.title),
                        severity=metadata.get("severity", "N/A"),
                        bailable=metadata.get("bailable", "N/A")
                    )
                    enriched_results.append(enriched)
                except Exception as e:
                    print(f"⚠ Failed to process section {section.section_id}: {e}")
                    # Fallback enrichment
                    enriched_results.append(EnrichedSection(
                        section_id=section.section_id,
                        title=section.title,
                        body=section.body,
                        page=section.page,
                        act=section.act,
                        common_crime_name="PROCEDURAL",
                        human_keywords=[section.title.lower()],
                        summary=section.title,
                        severity="N/A",
                        bailable="N/A"
                    ))
                    
        except Exception as e:
            print(f"⚠ Batch enrichment failed: {e}")
            print(f"Response: {response[:300] if 'response' in locals() else 'No response'}")
            
            # Fallback: use individual enrichment for this batch
            for section in batch:
                enriched_results.append(enrich_section_with_llm(section))
    
    return enriched_results


# ============================================================================
# STEP 3: VECTOR CONSTRUCTION (Rich Chunk)
# ============================================================================

def construct_rich_chunk(enriched: EnrichedSection) -> Document:
    """
    Constructs a "Composite String" for Vector DB.
    
    Format:
        search_document: Section 304: Snatching
        [Human Context] Keywords: chain snatching, mobile theft, grab and run
        [Legal Metadata] Severity: Cognizable. Bailable: No.
        [Summary] Punishes forcible grabbing of movable property.
        [Content] {Original Legal Text}
    
    Why: Creates strong semantic links between human language and legal provisions.
    """
    
    keywords_str = ", ".join(enriched.human_keywords)
    
    rich_content = f"""search_document: Section {enriched.section_id}: {enriched.title}
[Human Context] Keywords: {keywords_str}
[Legal Metadata] Severity: {enriched.severity}. Bailable: {enriched.bailable}.
[Summary] {enriched.summary}
[Content] {enriched.body}"""

    metadata = {
        "section_id": enriched.section_id,
        "act": enriched.act,
        "type": "legal_provision",
        "crime": enriched.common_crime_name,
        "title": enriched.title,
        "page": enriched.page,
        "severity": enriched.severity,
        "bailable": enriched.bailable,
        "keywords": keywords_str
    }
    
    return Document(page_content=rich_content, metadata=metadata)


# ============================================================================
# STEP 4: DUAL STORAGE COMMITMENT
# ============================================================================

def store_to_vector_db(documents: List[Document]) -> List[str]:
    """
    Stores Rich Chunks to ChromaDB.
    Returns list of UUIDs for each stored document.
    """
    try:
        dbs = core.get_dbs()
        all_uuids = []
        
        # Distribute across shards
        shard_docs = [[] for _ in range(core.NUM_SHARDS)]
        for i, doc in enumerate(documents):
            shard_idx = i % core.NUM_SHARDS
            shard_docs[shard_idx].append(doc)
        
        # Store in batches
        BATCH_SIZE = 32
        for shard_idx, docs in enumerate(shard_docs):
            if not docs:
                continue
                
            print(f"  Storing {len(docs)} chunks to shard {shard_idx}...")
            
            for j in range(0, len(docs), BATCH_SIZE):
                batch = docs[j:j + BATCH_SIZE]
                try:
                    ids = dbs[shard_idx].add_documents(batch)
                    all_uuids.extend(ids)
                except Exception as e:
                    print(f"  ✗ Batch {j//BATCH_SIZE + 1} failed: {e}")
        
        print(f"✓ Stored {len(all_uuids)} documents to Vector DB")
        return all_uuids
        
    except Exception as e:
        print(f"✗ Vector DB storage failed: {e}")
        return []


def store_to_json_map(enriched_sections: List[EnrichedSection], filename: str, act_name: str, file_id: str) -> Dict[str, Any]:
    """
    Creates/Updates the uploads_db.json with structured section map.
    
    Structure:
    {
        "file_id": "bns_act_2023",
        "filename": "BNS_Act_2023.pdf",
        "act": "BNS",
        "processed_at": "2025-01-21T08:43:21Z",
        "global_summary": "...",
        "sections": {
            "304": {
                "title": "Snatching",
                "summary": "...",
                "severity": "Cognizable",
                "bailable": "No",
                "chroma_uuid": "abc-123",
                "page": 112,
                "keywords": ["chain snatching", "mobile theft"]
            }
        }
    }
    """
    
    DB_FILE = "uploads_db.json"
    
    # Load existing database
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            db = json.loads(content) if content else {"documents": {}}
    else:
        db = {"documents": {}}
    
    # Generate global summary
    global_summary = f"{act_name} - Contains {len(enriched_sections)} legal provisions"
    
    # Build sections map - Using Target Schema Format
    # Each entry matches: { section_id, title, type, summary, keywords, severity, bailable, chroma_uuid, page_number }
    sections_map = []
    for section in enriched_sections:
        json_entry = {
            "section_id": section.section_id,          # From Regex
            "title": section.title,                    # From Regex
            "type": section.common_crime_name,         # From LLM (PENAL/PROCEDURAL)
            "summary": section.summary,                # From LLM
            "keywords": section.human_keywords,        # From LLM
            "severity": section.severity,              # From LLM
            "bailable": section.bailable,              # From LLM
            "chroma_uuid": section.chroma_uuid or "", # Link to Vector DB
            "page_number": section.page                # From Regex (page tracking)
        }
        sections_map.append(json_entry)
    
    # Create document entry - Changed "sections" to "sections_map" to match expected format
    document_entry = {
        "file_id": file_id,
        "filename": filename,
        "type": "statute",  # Document type identifier
        "act": act_name,
        "processed_at": datetime.now().isoformat(),
        "global_summary": global_summary,
        "total_sections": len(enriched_sections),
        "sections_map": sections_map  # Array of section objects (not a dict)
    }
    
    # Update database
    db["documents"][file_id] = document_entry
    
    # Save to file
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Updated JSON Map: {filename} → {len(sections_map)} sections")
    return document_entry


# ============================================================================
# MASTER ORCHESTRATION
# ============================================================================

def process_legal_document(
    file_path: str, 
    filename: str, 
    act_name: str = "UNKNOWN",
    status_callback=None
) -> Dict[str, Any]:
    """
    End-to-end smart processing of a legal document.
    
    Steps:
        1. Extract text from PDF
        2. Structural Segmentation → SectionCandidates
        3. Semantic Enrichment → EnrichedSections
        4. Vector Construction → Rich Chunks
        5. Dual Storage → Vector DB + JSON Map
    
    Returns:
        {
            "success": bool,
            "file_id": str,
            "sections_processed": int,
            "vector_uuids": List[str],
            "json_entry": Dict
        }
    """
    
    def send_status(msg: str):
        if status_callback:
            status_callback(msg)
        print(f"[SMART PROCESSOR] {msg}")
    
    try:
        send_status("🔍 Starting Smart Legal Document Processing...")
        
        # Generate file ID
        file_id = hashlib.md5(filename.encode()).hexdigest()[:12]
        
        # Step 1: Extract text
        send_status("📄 Extracting text from document...")
        from langchain_community.document_loaders import PyPDFLoader
        
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        full_text = "\n".join([page.page_content for page in pages])
        
        # Step 2: Structural Segmentation
        send_status(f"⚡ Applying Atomic Segmentation (Legal Boundaries)...")
        section_candidates = extract_sections_from_text(full_text, filename, act_name)
        
        send_status(f"✓ Extracted {len(section_candidates)} sections")
        
        # ============================================================================
        # OPTIMIZED BATCH PIPELINE (5x FASTER)
        # ============================================================================
        # Step 1: BATCH ENRICHMENT (Process 5 sections per LLM call)
        # Step 2: BATCH CHUNKING (Build all chunks at once)
        # Step 3: BATCH STORAGE (Store in groups of 32 with UUID tracking)
        # ============================================================================
        
        send_status("🧠 Starting FAST batch enrichment...")
        enriched_sections = enrich_sections_batch(section_candidates, batch_size=5)
        send_status(f"✓ Enriched {len(enriched_sections)} sections using batch processing")
        
        # Step 2: Construct all rich chunks
        send_status("🔨 Building vector chunks...")
        rich_documents = []
        for enriched in enriched_sections:
            rich_doc = construct_rich_chunk(enriched)
            rich_documents.append(rich_doc)
        send_status(f"✓ Built {len(rich_documents)} rich chunks")
        
        # Step 3: BATCH STORAGE with UUID capture
        send_status("💾 Storing to Vector DB in optimized batches...")
        dbs = core.get_dbs()
        
        # Distribute across shards
        shard_docs = [[] for _ in range(core.NUM_SHARDS)]
        shard_enriched = [[] for _ in range(core.NUM_SHARDS)]
        
        for i, (doc, enriched) in enumerate(zip(rich_documents, enriched_sections)):
            shard_idx = i % core.NUM_SHARDS
            shard_docs[shard_idx].append(doc)
            shard_enriched[shard_idx].append(enriched)
        
        # Store in batches per shard and capture UUIDs
        BATCH_SIZE = 32
        for shard_idx in range(core.NUM_SHARDS):
            if not shard_docs[shard_idx]:
                continue
                
            docs = shard_docs[shard_idx]
            enriched_list = shard_enriched[shard_idx]
            
            send_status(f"  Shard {shard_idx}: Storing {len(docs)} documents...")
            
            for batch_start in range(0, len(docs), BATCH_SIZE):
                batch_docs = docs[batch_start:batch_start + BATCH_SIZE]
                batch_enriched = enriched_list[batch_start:batch_start + BATCH_SIZE]
                
                try:
                    # Store batch and get UUIDs
                    doc_ids = dbs[shard_idx].add_documents(batch_docs)
                    
                    # Link UUIDs to enriched sections
                    for enriched, uuid in zip(batch_enriched, doc_ids):
                        enriched.chroma_uuid = uuid
                        
                    send_status(f"     ✓ Batch {batch_start//BATCH_SIZE + 1}: {len(doc_ids)} UUIDs captured")
                    
                except Exception as e:
                    send_status(f"     ✗ Batch storage failed: {e}")
                    # Set empty UUIDs on failure
                    for enriched in batch_enriched:
                        enriched.chroma_uuid = ""
        
        send_status(f"✓ Stored {len(enriched_sections)} sections with UUID tracking")
        
        # Step 5b: Store to JSON Map (now with all UUIDs already linked)
        send_status("📋 Updating JSON Map (Fast Brain)...")
        json_entry = store_to_json_map(enriched_sections, filename, act_name, file_id)
        
        send_status("✅ Smart Processing Complete!")
        
        # Clear cache
        core.clear_cache()
        
        return {
            "success": True,
            "file_id": file_id,
            "sections_processed": len(enriched_sections),
            "vector_uuids": [s.chroma_uuid for s in enriched_sections if s.chroma_uuid],
            "json_entry": json_entry,
            "message": f"Successfully processed {len(enriched_sections)} sections"
        }
        
    except Exception as e:
        send_status(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "message": "Processing failed"
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def detect_act_name(filename: str) -> str:
    """
    Attempts to detect the Act name from filename.
    
    Examples:
        "BNS_Act_2023.pdf" → "BNS"
        "IPC.pdf" → "IPC"
        "bharatiya_nyaya_sanhita.pdf" → "BNS"
    """
    
    filename_lower = filename.lower()
    
    # Mapping of keywords to Act names
    act_mappings = {
        'bns': 'BNS',
        'bharatiya nyaya sanhita': 'BNS',
        'ipc': 'IPC',
        'indian penal code': 'IPC',
        'crpc': 'CrPC',
        'code of criminal procedure': 'CrPC',
        'bnss': 'BNSS',
        'bharatiya nagarik suraksha sanhita': 'BNSS',
        'bsa': 'BSA',
        'bharatiya sakshya adhiniyam': 'BSA',
        'evidence act': 'IEA',
        'iea': 'IEA'
    }
    
    for keyword, act in act_mappings.items():
        if keyword in filename_lower:
            return act
    
    return "UNKNOWN"
