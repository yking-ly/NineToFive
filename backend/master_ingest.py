"""
Master Ingestion Pipeline - The Intelligent Router

This module automatically detects document types and routes them to the correct processor:
- STATUTES (Acts) → Section-based chunking with legal metadata
- JUDGMENTS (Cases) → Zone-based chunking with ratio decidendi extraction

Architecture:
    1. Document Type Detection (Router)
    2. Statute Processing (Section-aware splitting)
    3. Case Processing (Zone-based splitting)
    4. Dual Storage (Vector DB + JSON Map)
"""

import os
import re
import json
import uuid
import hashlib
from typing import List, Dict, Any, Tuple
from datetime import datetime

try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.docstore.document import Document

from langchain_community.document_loaders import PyPDFLoader

import core
import smart_processor  # Use existing statute processor


# ============================================================================
# ENRICHMENT ENGINE - The "Brain" that talks to Qwen
# ============================================================================

class EnrichmentEngine:
    """
    LLM-powered metadata extraction engine.
    Handles both Statute and Case enrichment with different prompts.
    """
    
    def __init__(self):
        self.llm = core.get_llm()
    
    def identify_doc_type(self, text_sample: str) -> str:
        """
        Router Logic: Determines if document is an Act or a Case.
        
        Returns: "STATUTE" or "JUDGMENT"
        """
        text_lower = text_sample.lower()
        
        # Case indicators
        case_indicators = [
            "versus", "vs.", "v.", "appellant", "respondent", 
            "writ petition", "bench", "hon'ble", "judgment",
            "petitioner", "criminal appeal", "civil appeal",
            "supreme court", "high court", "coram"
        ]
        
        # Statute indicators
        statute_indicators = [
            "act no.", "section 1", "chapter i", "commencement",
            "short title", "definitions", "the act", "ordinance",
            "enacted by parliament", "legislation", "parliament"
        ]
        
        case_score = sum(1 for indicator in case_indicators if indicator in text_lower)
        statute_score = sum(1 for indicator in statute_indicators if indicator in text_lower)
        
        # Additional pattern matching
        if re.search(r'\b(?:W\.?P\.?|Crl\.?A\.?|C\.?A\.?)\s*(?:No\.?)?\s*\d+', text_sample):
            case_score += 3
        
        if re.search(r'(?:ACT|BILL)\s+(?:NO\.?)?\s*\d+\s+OF\s+\d{4}', text_sample, re.IGNORECASE):
            statute_score += 3
        
        print(f"📊 Document Type Detection: Statute={statute_score}, Case={case_score}")
        
        if case_score > statute_score:
            return "JUDGMENT"
        return "STATUTE"
    
    def enrich_statute_section(self, section_id: str, title: str, content: str) -> Dict[str, Any]:
        """
        Generates metadata for Statute Sections using LLM.
        
        Returns:
            {
                "common_name": str,
                "keywords": List[str],
                "summary": str,
                "severity": str,
                "bailable": str
            }
        """
        
        prompt = f"""You are a legal metadata extractor. Analyze this legal section and return ONLY a valid JSON object.

SECTION:
Section {section_id}: {title}
{content[:1200]}

INSTRUCTIONS:
Return a JSON object with these exact keys:
{{
    "common_name": "Simple name for this provision (or 'General Provision' if not crime-related)",
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "summary": "One sentence simple English explanation",
    "severity": "Cognizable/Non-Cognizable/N/A",
    "bailable": "Yes/No/Depends/N/A"
}}

IMPORTANT: Return ONLY the JSON object. No explanations.
"""

        try:
            response = core.safe_llm_invoke(prompt, max_tokens=300, temperature=0.3)
            response = response.replace("```json", "").replace("```", "").strip()
            
            metadata = json.loads(response)
            
            # Validate and return
            return {
                "common_name": metadata.get("common_name", "Legal Provision"),
                "keywords": metadata.get("keywords", [title.lower()])[:5],
                "summary": metadata.get("summary", title),
                "severity": metadata.get("severity", "N/A"),
                "bailable": metadata.get("bailable", "N/A")
            }
            
        except Exception as e:
            print(f"⚠ Enrichment failed for Section {section_id}: {e}")
            return {
                "common_name": "Legal Provision",
                "keywords": [title.lower(), section_id],
                "summary": title,
                "severity": "N/A",
                "bailable": "N/A"
            }
    
    def enrich_case_zone(self, zone_name: str, content: str, case_name: str) -> Dict[str, Any]:
        """
        Generates metadata for Case Judgment Zones using LLM.
        
        Returns:
            {
                "legal_topic": str,
                "ratio": str,
                "summary": str,
                "precedent_value": str
            }
        """
        
        prompt = f"""You are a legal case analyzer. Analyze this section from a judgment and return ONLY a valid JSON object.

CASE: {case_name}
SECTION: {zone_name}
CONTENT:
{content[:1500]}

INSTRUCTIONS:
Return a JSON object with these exact keys:
{{
    "legal_topic": "Main legal issue discussed (e.g., 'Bail Jurisprudence', 'Evidence Standards')",
    "ratio": "The core legal principle/ratio decidendi in one sentence",
    "summary": "Simple explanation of what this section discusses",
    "precedent_value": "High/Medium/Low/Procedural"
}}

IMPORTANT: Return ONLY the JSON object. No explanations.
"""

        try:
            response = core.safe_llm_invoke(prompt, max_tokens=350, temperature=0.3)
            response = response.replace("```json", "").replace("```", "").strip()
            
            metadata = json.loads(response)
            
            return {
                "legal_topic": metadata.get("legal_topic", "General Discussion"),
                "ratio": metadata.get("ratio", "See full text for details"),
                "summary": metadata.get("summary", f"Discussion in {zone_name} section"),
                "precedent_value": metadata.get("precedent_value", "Medium")
            }
            
        except Exception as e:
            print(f"⚠ Zone enrichment failed: {e}")
            return {
                "legal_topic": "Legal Analysis",
                "ratio": "See full judgment text",
                "summary": f"{zone_name} section of the judgment",
                "precedent_value": "Medium"
            }

    def enrich_batch(self, section_batch: List[Tuple[str, str, str]]) -> List[Dict[str, Any]]:
        """
        Enriches a batch of sections in a single LLM call.
        
        Input: List of 5 tuples [(id, title, text), ...]
        Output: List of 5 Metadata Objects
        """
        # Construct a combined prompt
        combined_text = ""
        for idx, (sid, stitle, stext) in enumerate(section_batch):
            combined_text += f"\n--- ITEM {idx+1} ---\nSection {sid}: {stitle}\n{stext[:500]}..."

        prompt = f"""You are a legal metadata extractor. Analyze these {len(section_batch)} legal sections and return ONLY a JSON array.

Input Sections:
{combined_text}

Return a JSON array with {len(section_batch)} objects. Each object must have:
- type: "PENAL" or "PROCEDURAL"
- summary: One clear sentence
- keywords: Array of 5 relevant terms
- severity: "Cognizable" or "Non-Cognizable" or "N/A"
- bailable: "Yes" or "No" or "Depends" or "N/A"

IMPORTANT: Return ONLY the JSON array, nothing else. No explanations.
Example format: [{{"type": "PENAL", "summary": "...", "keywords": ["...", "..."], "severity": "Cognizable", "bailable": "No"}}, ...]
"""
        
        try:
            response = core.safe_llm_invoke(prompt, max_tokens=1500, temperature=0.2)
            
            # Clean response aggressively
            response = response.strip()
            
            # Remove markdown code blocks
            response = response.replace("```json", "").replace("```", "")
            
            # Find the JSON array bounds
            start_idx = response.find('[')
            end_idx = response.rfind(']')
            
            if start_idx == -1 or end_idx == -1:
                raise ValueError(f"No JSON array found in response: {response[:200]}")
            
            # Extract only the array portion
            json_str = response[start_idx:end_idx + 1].strip()
            
            # Parse JSON
            metadata_list = json.loads(json_str)
            
            if not isinstance(metadata_list, list):
                raise ValueError("Parsed result is not a list")
            
            # Validate we got the right number of items
            if len(metadata_list) != len(section_batch):
                print(f"⚠ Warning: Expected {len(section_batch)} items, got {len(metadata_list)}")
                
            return metadata_list
            
        except json.JSONDecodeError as e:
            print(f"⚠ JSON parsing failed: {e}")
            print(f"Response excerpt: {response[:500] if 'response' in locals() else 'No response'}")
            # Fallback: Return empty dicts
            return [{} for _ in section_batch]
        except Exception as e:
            print(f"⚠ Batch enrichment failed: {e}")
            # Fallback: Return empty dicts so processor uses defaults
            return [{} for _ in section_batch]


# ============================================================================
# STATUTE PROCESSOR - Batch Optimized
# ============================================================================

class StatuteProcessor:
    """
    Processes Acts/Statutes using Section-Based processing.
    Features: Batch Enrichment for 5x speedup.
    """
    
    def __init__(self, enricher: EnrichmentEngine):
        self.enricher = enricher
        self.pattern = re.compile(
            r'(?m)^(?:Section|Article|Sec\.?)\s*(\d+[A-Z]*)\s*\.?\s*[:\-\–]?\s*(.+?)$',
            re.IGNORECASE
        )

    def _regex_split(self, text):
        """Helper to extract (ID, Title, Content) tuples"""
        matches = list(re.finditer(self.pattern, text))
        results = []
        if not matches:
             return []
             
        for i, match in enumerate(matches):
            sec_id = match.group(1).strip()
            sec_title = match.group(2).strip().split('\n')[0]
            start = match.start()
            end = matches[i+1].start() if i+1 < len(matches) else len(text)
            content = text[start:end].strip()
            results.append((sec_id, sec_title, content))
        return results

    def process(self, raw_docs, filename, drive_metadata):
        full_text = "\n".join([d.page_content for d in raw_docs])
        
        # 1. REGEX SPLIT (Atomic Segmentation)
        # Returns raw text blocks: [ ("101", "Title", "Text..."), ... ]
        raw_sections = self._regex_split(full_text) 
        
        if not raw_sections:
            print(f"⚠ No sections found in {filename}. Chunking as generic document.")
            # Fallback to simple chunking if needed, or return empty
            return [], {"sections_map": []}

        smart_chunks = []
        json_map = []
        
        # 2. BATCH ENRICHMENT LOOP (The Speed Optimization)
        # Process 5 sections at a time
        BATCH_SIZE = 5
        
        print(f"📚 Processing {len(raw_sections)} sections in batches of {BATCH_SIZE}...")
        
        for i in range(0, len(raw_sections), BATCH_SIZE):
            batch = raw_sections[i : i + BATCH_SIZE]
            
            # CALL LLM ONCE for 5 sections
            enriched_batch_metadata = self.enricher.enrich_batch(batch)
            
            # Process the results
            for j, section_raw in enumerate(batch):
                sec_id, sec_title, content = section_raw
                
                # Retrieve metadata for this specific section from the batch result
                # Fallback to defaults if LLM messed up the array order
                meta = enriched_batch_metadata[j] if j < len(enriched_batch_metadata) else {}
                
                # 3. CONSTRUCT COMPOSITE CHUNK
                chunk_uuid = str(uuid.uuid4())
                
                # Handle missing keys gracefully
                keywords = meta.get('keywords', meta.get('human_keywords', [sec_title]))
                if isinstance(keywords, str): keywords = [keywords]
                
                rich_content = (
                    f"Section {sec_id}: {sec_title}\n"
                    f"Type: {meta.get('type', 'PENAL')}\n"
                    f"Summary: {meta.get('summary', sec_title)}\n"
                    f"Keywords: {', '.join(keywords)}\n"
                    f"Status: {meta.get('severity', 'N/A')}, Bailable: {meta.get('bailable', 'N/A')}\n"
                    f"Content: {content}"
                )
                
                # Add to Vector List
                smart_chunks.append(Document(
                    page_content=rich_content,
                    metadata={
                        "source": filename,
                        "section_id": sec_id,
                        "chunk_id": chunk_uuid,
                        "act": drive_metadata.get('act', "UNKNOWN"), 
                        **meta
                    }
                ))
                
                # Add to JSON Map List
                json_map.append({
                    "section_id": sec_id,
                    "title": sec_title,
                    "type": meta.get('type', 'PENAL'),
                    "summary": meta.get('summary', ''),
                    "chroma_uuid": chunk_uuid,
                    "page_number": 1 # Simplified for now
                })

        return smart_chunks, {"sections_map": json_map, **drive_metadata}


# ============================================================================
# CASE PROCESSOR - Zone-Based Splitting for Judgments
# ============================================================================

class CaseProcessor:
    """
    Processes Court Judgments using Zone-Based chunking.
    
    Zones: Facts → Issues → Arguments → Reasoning → Verdict
    """
    
    def __init__(self, enricher: EnrichmentEngine):
        self.enricher = enricher
    
    def detect_zone(self, text: str, prev_zone: str) -> str:
        """
        Detects the current zone of the judgment.
        Uses keyword matching and position heuristics.
        """
        text_lower = text.lower()
        
        # Zone detection patterns
        if any(kw in text_lower[:300] for kw in ["fact", "factual background", "brief facts"]):
            return "Facts"
        
        if any(kw in text_lower[:200] for kw in ["issue", "question", "point for determination"]):
            return "Issues"
        
        if any(kw in text_lower[:200] for kw in ["argument", "submission", "contention", "counsel argued"]):
            return "Arguments"
        
        if any(kw in text_lower[:200] for kw in ["reasoning", "analysis", "discussion", "we find", "in our opinion"]):
            return "Reasoning"
        
        if any(kw in text_lower[:200] for kw in ["order", "verdict", "judgment", "we hold", "conclusion", "disposed of"]):
            return "Verdict"
        
        # Default: continue previous zone
        return prev_zone
    
    def extract_case_metadata(self, full_text: str) -> Dict[str, str]:
        """
        Extracts case identification metadata from judgment text.
        """
        lines = full_text.split('\n')[:50]  # Check first 50 lines
        text_sample = '\n'.join(lines)
        
        # Extract case number
        case_num_match = re.search(
            r'(?:W\.?P\.?|Crl\.?A\.?|C\.?A\.?|S\.?L\.?P\.?)\s*(?:\((?:Crl|Civ)\))?\s*(?:No\.?)?\s*(\d+(?:/\d+)?(?:\s+of\s+\d{4})?)',
            text_sample,
            re.IGNORECASE
        )
        case_number = case_num_match.group(0) if case_num_match else "Unknown"
        
        # Extract parties
        vs_match = re.search(r'(.+?)\s+(?:v\.|vs\.?|versus)\s+(.+?)(?:\n|$)', text_sample, re.IGNORECASE)
        if vs_match:
            petitioner = vs_match.group(1).strip()
            respondent = vs_match.group(2).strip()
        else:
            petitioner = "Unknown"
            respondent = "Unknown"
        
        # Extract court
        court = "Unknown Court"
        if "supreme court" in text_sample.lower():
            court = "Supreme Court of India"
        elif "high court" in text_sample.lower():
            hc_match = re.search(r'(\w+)\s+high court', text_sample.lower())
            if hc_match:
                court = f"{hc_match.group(1).title()} High Court"
        
        return {
            "case_number": case_number,
            "petitioner": petitioner,
            "respondent": respondent,
            "court": court
        }
    
    def process(self, raw_docs: List[Document], filename: str) -> Tuple[List[Document], Dict[str, Any]]:
        """
        Main case processing logic.
        
        Returns:
            (smart_chunks, json_metadata)
        """
        print(f"⚖️  Processing {filename} as JUDGMENT...")
        
        # Merge all pages
        full_text = "\n".join([doc.page_content for doc in raw_docs])
        
        # Extract case metadata
        case_meta = self.extract_case_metadata(full_text)
        case_name = f"{case_meta['petitioner']} vs. {case_meta['respondent']}"
        
        print(f"   Case: {case_name}")
        print(f"   Number: {case_meta['case_number']}")
        
        # Split by paragraphs (preserve numbering)
        # Pattern matches: [1], 2., 3), etc.
        segments = re.split(r'(?m)^(\[?\d+\]?\.?)\s+', full_text)
        
        smart_chunks = []
        zones_map = {}
        
        current_buffer = ""
        current_zone = "Facts"  # Default starting zone
        chunk_counter = 0
        
        for i, segment in enumerate(segments):
            # Skip pure numbers
            if i % 2 == 1:  # These are the paragraph numbers
                continue
            
            current_buffer += segment + " "
            
            # Process when buffer reaches substantial size
            if len(current_buffer) > 2000 or i >= len(segments) - 2:
                # Detect zone
                current_zone = self.detect_zone(current_buffer, current_zone)
                
                # Enrich with LLM
                enrichment = self.enricher.enrich_case_zone(
                    zone_name=current_zone,
                    content=current_buffer,
                    case_name=case_name
                )
                
                # Construct Rich Document
                rich_content = f"""Case Law Document
Case Name: {case_name}
Case Number: {case_meta['case_number']}
Court: {case_meta['court']}
Section: {current_zone}

[Legal Topic]: {enrichment['legal_topic']}
[Ratio Decidendi]: {enrichment['ratio']}
[Summary]: {enrichment['summary']}
[Precedent Value]: {enrichment['precedent_value']}

Full Text:
{current_buffer}"""

                chunk_id = str(uuid.uuid4())
                
                doc = Document(
                    page_content=rich_content,
                    metadata={
                        "source": filename,
                        "type": "judgment",
                        "zone": current_zone,
                        "case_name": case_name,
                        "case_number": case_meta['case_number'],
                        "court": case_meta['court'],
                        "chunk_id": chunk_id,
                        "legal_topic": enrichment['legal_topic'],
                        "ratio": enrichment['ratio'],
                        "precedent_value": enrichment['precedent_value']
                    }
                )
                
                smart_chunks.append(doc)
                chunk_counter += 1
                
                # Store first chunk of each zone in zones_map
                if current_zone not in zones_map:
                    zones_map[current_zone] = {
                        "summary": enrichment['summary'],
                        "ratio": enrichment['ratio'],
                        "chroma_uuid": chunk_id,
                        "legal_topic": enrichment['legal_topic']
                    }
                
                current_buffer = ""
        
        print(f"✓ Created {len(smart_chunks)} zone-based chunks")
        
        # Build JSON structure
        json_data = {
            "case_metadata": case_meta,
            "zones_map": zones_map,
            "total_zones": len(zones_map)
        }
        
        return smart_chunks, json_data


# ============================================================================
# MASTER PIPELINE - The Orchestrator
# ============================================================================

class MasterIngestPipeline:
    """
    The Master Orchestrator that:
    1. Detects document type
    2. Routes to appropriate processor
    3. Stores to dual-brain system
    """
    
    def __init__(self):
        self.enricher = EnrichmentEngine()
        self.statute_processor = StatuteProcessor(self.enricher)
        self.case_processor = CaseProcessor(self.enricher)
        self.json_db_path = "uploads_db.json"
    
    def run(self, file_path: str, original_filename: str = None, drive_metadata: Dict = None, status_callback=None) -> Dict[str, Any]:
        """
        Master execution logic.
        
        Args:
            file_path: Path to PDF file
            original_filename: Filename (defaults to basename of file_path)
            drive_metadata: Optional dict with Drive URL, thumbnail, act name, etc.
            status_callback: Optional callback for status updates
        
        Returns:
            {
                "success": bool,
                "doc_type": "STATUTE" | "JUDGMENT",
                "chunks_created": int,
                "file_id": str,
                "message": str
            }
        """
        
        # Default filename to basename if not provided
        if not original_filename:
            original_filename = os.path.basename(file_path)
        
        # Initialize drive_metadata if not provided
        if not drive_metadata:
            drive_metadata = {}
        
        def send_status(msg: str):
            if status_callback:
                status_callback(msg)
            print(f"[MASTER INGEST] {msg}")
        
        try:
            send_status(f"📄 Loading {original_filename}...")
            
            # Load PDF
            loader = PyPDFLoader(file_path)
            raw_docs = loader.load()
            
            if not raw_docs:
                return {
                    "success": False,
                    "error": "Failed to load PDF",
                    "message": "Document appears to be empty or corrupted"
                }
            
            # A. DETECT DOCUMENT TYPE (Router)
            send_status("🔍 Analyzing document type...")
            intro_text = raw_docs[0].page_content[:2000]
            doc_type = self.enricher.identify_doc_type(intro_text)
            
            send_status(f"✓ Detected: {doc_type}")
            
            # B. ROUTE TO APPROPRIATE PROCESSOR
            if doc_type == "STATUTE":
                # Use batch-optimized StatuteProcessor
                send_status("📚 Routing to Batch-Optimized Statute Processor...")
                
                # Detect act name from metadata or filename
                act_name = drive_metadata.get('act') or smart_processor.detect_act_name(original_filename)
                drive_metadata['act'] = act_name
                
                # Process with batch enrichment
                smart_chunks, json_data = self.statute_processor.process(
                    raw_docs=raw_docs,
                    filename=original_filename,
                    drive_metadata=drive_metadata
                )
                
                # C. STORE TO VECTOR DB
                send_status(f"💾 Storing {len(smart_chunks)} chunks to Vector DB...")
                
                dbs = core.get_dbs()
                all_uuids = []
                
                # Distribute across shards
                shard_docs = [[] for _ in range(core.NUM_SHARDS)]
                for i, doc in enumerate(smart_chunks):
                    shard_idx = i % core.NUM_SHARDS
                    shard_docs[shard_idx].append(doc)
                
                BATCH_SIZE = 32
                for shard_idx, docs in enumerate(shard_docs):
                    if not docs:
                        continue
                    
                    for j in range(0, len(docs), BATCH_SIZE):
                        batch = docs[j:j + BATCH_SIZE]
                        try:
                            ids = dbs[shard_idx].add_documents(batch)
                            all_uuids.extend(ids)
                        except Exception as e:
                            print(f"  ✗ Batch storage failed: {e}")
                
                # D. UPDATE JSON DB
                send_status("📋 Updating Fast Brain (JSON Map)...")
                file_id = hashlib.md5(original_filename.encode()).hexdigest()[:12]
                
                self._update_json_db(
                    file_id=file_id,
                    filename=original_filename,
                    doc_type=doc_type,
                    json_data=json_data,
                    vector_uuids=all_uuids
                )
                
                # Clear cache
                core.clear_cache()
                
                send_status("✅ Processing Complete!")
                
                return {
                    "success": True,
                    "doc_type": "STATUTE",
                    "chunks_created": len(smart_chunks),
                    "file_id": file_id,
                    "message": f"Successfully processed statute with {len(smart_chunks)} sections",
                    "processing_method": "batch_statute_processor"
                }
            
            else:  # JUDGMENT
                send_status("⚖️  Routing to Case Processor...")
                
                # Process as case
                smart_chunks, json_data = self.case_processor.process(raw_docs, original_filename)
                
                # C. STORE TO VECTOR DB
                send_status(f"💾 Storing {len(smart_chunks)} chunks to Vector DB...")
                
                dbs = core.get_dbs()
                all_uuids = []
                
                # Distribute across shards
                shard_docs = [[] for _ in range(core.NUM_SHARDS)]
                for i, doc in enumerate(smart_chunks):
                    shard_idx = i % core.NUM_SHARDS
                    shard_docs[shard_idx].append(doc)
                
                BATCH_SIZE = 32
                for shard_idx, docs in enumerate(shard_docs):
                    if not docs:
                        continue
                    
                    for j in range(0, len(docs), BATCH_SIZE):
                        batch = docs[j:j + BATCH_SIZE]
                        try:
                            ids = dbs[shard_idx].add_documents(batch)
                            all_uuids.extend(ids)
                        except Exception as e:
                            print(f"  ✗ Batch storage failed: {e}")
                
                # D. UPDATE JSON DB
                send_status("📋 Updating Fast Brain (JSON Map)...")
                file_id = hashlib.md5(original_filename.encode()).hexdigest()[:12]
                
                self._update_json_db(
                    file_id=file_id,
                    filename=original_filename,
                    doc_type=doc_type,
                    json_data=json_data,
                    vector_uuids=all_uuids
                )
                
                # Clear cache
                core.clear_cache()
                
                send_status("✅ Processing Complete!")
                
                return {
                    "success": True,
                    "doc_type": "JUDGMENT",
                    "chunks_created": len(smart_chunks),
                    "file_id": file_id,
                    "message": f"Successfully processed judgment with {len(smart_chunks)} zone chunks",
                    "processing_method": "case_processor",
                    "zones": list(json_data['zones_map'].keys())
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
    
    def _update_json_db(
        self,
        file_id: str,
        filename: str,
        doc_type: str,
        json_data: Dict[str, Any],
        vector_uuids: List[str]
    ):
        """
        Updates uploads_db.json with document metadata.
        """
        
        # Load existing
        if os.path.exists(self.json_db_path):
            with open(self.json_db_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                db = json.loads(content) if content else {"documents": {}}
        else:
            db = {"documents": {}}
        
        # Create entry
        if doc_type == "JUDGMENT":
            entry = {
                "file_id": file_id,
                "filename": filename,
                "type": "judgment",
                "processed_at": datetime.now().isoformat(),
                "case_metadata": json_data.get("case_metadata", {}),
                "zones": json_data.get("zones_map", {}),
                "total_zones": json_data.get("total_zones", 0),
                "vector_uuids": vector_uuids[:10]  # Store sample for reference
            }
        else:
            entry = json_data  # Statute processor already creates proper format
        
        db["documents"][file_id] = entry
        
        # Save
        with open(self.json_db_path, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Updated JSON Map: {filename}")


# ============================================================================
# CONVENIENCE WRAPPER
# ============================================================================

def smart_ingest(file_path: str, filename: str, status_callback=None) -> Dict[str, Any]:
    """
    Convenience function for smart ingestion.
    
    Usage:
        result = smart_ingest("uploads/document.pdf", "document.pdf")
        if result['success']:
            print(f"Processed as {result['doc_type']}")
    """
    pipeline = MasterIngestPipeline()
    return pipeline.run(file_path, filename, status_callback)
