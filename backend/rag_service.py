import sys
import os
import re
from pathlib import Path

# retrieval_engine is now at backend/retrieval_engine/
from retrieval_engine.vector_store.chroma_client import ChromaDBClient
from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator
from cache_service import CacheService
from llm_service import OllamaService

class RAGService:
    # Regex to detect section numbers WITH context (IPC/BNS)
    # Group 1: context (ipc/bns/section/etc), Group 2: section number
    SECTION_PATTERN = re.compile(
        r'(ipc|bns|section|sec\.?|धारा)\s*(\d+(?:\s*\(\d+\))?(?:\s*[A-Za-z])?)',
        re.IGNORECASE
    )
    
    def __init__(self):
        self.chroma = ChromaDBClient()
        self.cache = CacheService()  # Initialize Redis cache
        self.llm = OllamaService()   # Initialize Ollama LLM
        print("[RAG Service] ChromaDB Client Initialized")
    
    def extract_section_info(self, query: str) -> dict:
        """
        Extract section number and context (IPC/BNS/ambiguous) from query.
        
        Returns:
            dict with keys:
                - section: The section number (e.g., "302")
                - section_base: Base section without sub-clause (e.g., "103" from "103(1)")
                - context: "ipc", "bns", or "ambiguous"
        """
        match = self.SECTION_PATTERN.search(query)
        if match:
            context_word = match.group(1).lower()
            section = match.group(2).strip()
            section = re.sub(r'\s+', '', section)  # "302 (1)" -> "302(1)"
            
            # Extract base section number (for DB filtering)
            # "103(1)" -> "103", "302A" -> "302A", "420" -> "420"
            section_base = re.match(r'(\d+[A-Za-z]?)', section)
            section_base = section_base.group(1) if section_base else section
            
            # Determine context - check context_word first, then full query
            query_lower = query.lower()
            if context_word == 'ipc' or ('ipc' in query_lower and 'bns' not in query_lower):
                context = 'ipc'
            elif context_word == 'bns' or ('bns' in query_lower and 'ipc' not in query_lower):
                context = 'bns'
            else:
                # Both IPC and BNS mentioned, or neither - truly ambiguous
                context = 'ambiguous'
            
            return {"section": section, "section_base": section_base, "context": context}
        return None

    def query_statutes(self, query_text: str, n_results: int = 3, collections: list = None, language: str = "en"):
        """
        Query IPC, BNS, and Mapping collections with Hybrid Search + Redis Cache.
        
        If a section number is detected in the query, uses metadata filtering
        for exact matching. Context-aware: distinguishes between IPC/BNS references.
        
        Uses Redis cache for <1ms response on repeated queries.
        
        Args:
            query_text: The search query.
            n_results: Number of results per collection.
            collections: Optional list of collections to search. 
                         Valid values: ["ipc", "bns", "mapping"].
                         If None, searches all collections.
            language: Language filter - "en" (English), "hi" (Hindi), or "all".
        """
        # Default to all collections if not specified
        # NOTE: case_law disabled - collection corrupted, needs re-ingestion
        if collections is None or len(collections) == 0:
            collections = ["ipc", "bns", "mapping"]
        
        # Normalize to lowercase
        collections = [c.lower() for c in collections]
        
        # =====================================================================
        # CACHE CHECK: Return cached response if available
        # =====================================================================
        cached = self.cache.get_response(query_text, collections)
        if cached:
            return cached  # Cache HIT - return immediately (<1ms)
        
        results = {
            "ipc": [],
            "bns": [],
            "mapping": [],
            "case_law": [],
            "quick_mapping": []  # Instant lookup results
        }
        
        # =====================================================================
        # QUICK MAPPING: Check for instant IPC/BNS section lookup
        # =====================================================================
        section_info = self.extract_section_info(query_text)
        if section_info:
            section_num = section_info["section_base"]
            context = section_info.get("context", "")
            
            # Try quick lookup based on context
            quick_result = None
            if context == "ipc" or "ipc" in query_text.lower():
                quick_result = self.cache.quick_lookup_ipc(section_num)
            elif context == "bns" or "bns" in query_text.lower():
                quick_result = self.cache.quick_lookup_bns(section_num)
            else:
                # Try both
                quick_result = self.cache.quick_lookup_ipc(section_num)
                if not quick_result:
                    quick_result = self.cache.quick_lookup_bns(section_num)
            
            if quick_result:
                results["quick_mapping"].append(quick_result)
                print(f"[RAG] QUICK MAPPING: Found instant match for section {section_num}")
        
        # HYBRID SEARCH: Extract section info
        section_info = self.extract_section_info(query_text)
        
        # Build metadata filters based on context
        ipc_filter = None
        bns_filter = None
        mapping_filter = None
        
        if section_info:
            section_num = section_info["section"]
            section_base = section_info["section_base"]  # Use base for DB filtering
            context = section_info["context"]
            print(f"[RAG] Hybrid Search: Detected section '{section_num}' (base: {section_base}, context: {context})")
            
            if context == "ipc":
                # User explicitly said "IPC 302"
                ipc_filter = {"section_number": section_base}
                # Search mapping for IPC -> BNS translation
                mapping_filter = {"ipc_section": section_base}
                # Don't filter BNS (semantic search will find related content)
                
            elif context == "bns":
                # User explicitly said "BNS 103"
                bns_filter = {"section_number": section_base}
                # Search mapping for BNS -> IPC translation
                mapping_filter = {"bns_section": section_base}
                # Don't filter IPC
                
            else:
                # Ambiguous: "Section 302" - assume IPC context (most common usage)
                ipc_filter = {"section_number": section_base}
                # Search mapping for both directions
                mapping_filter = {
                    "$or": [
                        {"ipc_section": section_base},
                        {"bns_section": section_base}
                    ]
                }
                # DON'T filter BNS by this number (would give wrong section)
        
        # Build language filter if not "all"
        def add_language_filter(base_filter, lang):
            """Combine existing filter with language filter."""
            if lang == "all":
                return base_filter
            lang_filter = {"language": lang}
            if base_filter is None:
                return lang_filter
            # If base filter already has $and, append to it
            if "$and" in base_filter:
                return {"$and": base_filter["$and"] + [lang_filter]}
            # Otherwise combine with $and
            return {"$and": [base_filter, lang_filter]}
        
        # If exact section is detected, show all languages (don't miss data)
        # Only apply language filter for semantic search
        effective_language = language if not section_info else "all"
        print(f"[RAG] Language filter: {language} (effective: {effective_language})")
        
        # 1. Search IPC (if requested)
        if "ipc" in collections:
            try:
                combined_filter = add_language_filter(ipc_filter, effective_language)
                print(f"[RAG] IPC filter: {combined_filter}")
                ipc_res = self.chroma.query("ipc", query_text, n_results, where=combined_filter)
                if ipc_res['ids']:
                    for i, doc_id in enumerate(ipc_res['ids']):
                        results["ipc"].append({
                            "id": doc_id,
                            "text": ipc_res['documents'][i],
                            "metadata": ipc_res['metadatas'][i],
                            "score": ipc_res['distances'][i] if ipc_res['distances'] else 0
                        })
            except Exception as e:
                print(f"[RAG Error] IPC Query failed: {e}")

        # 2. Search BNS (if requested)
        if "bns" in collections:
            try:
                combined_filter = add_language_filter(bns_filter, effective_language)
                bns_res = self.chroma.query("bns", query_text, n_results, where=combined_filter)
                if bns_res['ids']:
                    for i, doc_id in enumerate(bns_res['ids']):
                        results["bns"].append({
                            "id": doc_id,
                            "text": bns_res['documents'][i],
                            "metadata": bns_res['metadatas'][i],
                            "score": bns_res['distances'][i] if bns_res['distances'] else 0
                        })
            except Exception as e:
                print(f"[RAG Error] BNS Query failed: {e}")

        # 3. Search Mapping (if requested)
        if "mapping" in collections:
            try:
                map_res = self.chroma.query("mapping", query_text, n_results, where=mapping_filter)
                if map_res['ids']:
                    for i, doc_id in enumerate(map_res['ids']):
                        results["mapping"].append({
                            "id": doc_id,
                            "text": map_res['documents'][i],
                            "metadata": map_res['metadatas'][i],
                            "score": map_res['distances'][i] if map_res['distances'] else 0
                        })
            except Exception as e:
                print(f"[RAG Error] Mapping Query failed: {e}")

        # 4. Search Case Law (if requested)
        if "case_law" in collections:
            try:
                # Build case law filter based on detected sections
                case_law_filter = None
                if section_info:
                    section_base = section_info["section_base"]
                    # Search for cases that mention this section
                    # The sections_mentioned field is comma-separated, so we use $contains
                    case_law_filter = {"sections_mentioned": {"$contains": section_base}}
                
                print(f"[RAG] Case Law filter: {case_law_filter}")
                case_res = self.chroma.query("case_law", query_text, n_results, where=case_law_filter)
                print(f"[RAG] Case Law raw results: {len(case_res['ids'])} found")
                
                if case_res['ids']:
                    for i, doc_id in enumerate(case_res['ids']):
                        results["case_law"].append({
                            "id": doc_id,
                            "text": case_res['documents'][i],
                            "metadata": case_res['metadatas'][i],
                            "score": case_res['distances'][i] if case_res['distances'] else 0
                        })
                    print(f"[RAG] Case Law: Found {len(case_res['ids'])} relevant cases")
            except Exception as e:
                print(f"[RAG Error] Case Law Query failed: {e}")

        # =====================================================================
        # CACHE STORE: Save results for future requests
        # =====================================================================
        self.cache.set_response(query_text, collections, results)
        
        return results
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of input text.
        Returns language code: 'hi' for Hindi, 'en' for English, 'hinglish' for romanized Hindi.
        """
        # First check for Hinglish (romanized Hindi in English letters)
        if self.is_hinglish(text):
            return 'hinglish'
        
        try:
            lang = detect(text)
            return lang
        except LangDetectException:
            return 'en'  # Default to English if detection fails
    
    def is_hinglish(self, text: str) -> bool:
        """
        Detect if text is Hinglish (Hindi written in English/Roman letters).
        Uses common Hindi words that appear in romanized form.
        """
        # Common Hindi words in romanized form
        hinglish_words = [
            'kya', 'hai', 'hain', 'ka', 'ki', 'ke', 'ko', 'se', 'me', 'mein',
            'aur', 'ya', 'nahi', 'nahin', 'kaise', 'kab', 'kahan', 'kaun',
            'saza', 'dhara', 'kanoon', 'kanooni', 'jurm', 'apradh', 'dand',
            'hatya', 'chori', 'dhoka', 'maar', 'pitai', 'lagao', 'bataiye',
            'batao', 'samjhao', 'samajh', 'matlab', 'arth', 'paribhasha',
            'mujhe', 'humein', 'unko', 'usko', 'isko', 'yeh', 'woh', 'wo',
            'agar', 'toh', 'phir', 'lekin', 'par', 'kyunki', 'isliye'
        ]
        
        text_lower = text.lower()
        words = re.findall(r'\b[a-zA-Z]+\b', text_lower)
        
        if len(words) < 2:
            return False
        
        # Count how many Hinglish words are present
        hinglish_count = sum(1 for word in words if word in hinglish_words)
        
        # If more than 20% of words are Hinglish, classify as Hinglish
        return hinglish_count >= 2 or (hinglish_count / len(words)) > 0.2
    
    def translate_hinglish_to_english(self, text: str) -> str:
        """
        Translate Hinglish (romanized Hindi) to English using Ollama.
        """
        if not self.llm.enabled:
            return text  # Return original if LLM not available
        
        prompt = f"""Convert this Hinglish (Hindi written in English letters) to proper English.
Only output the English translation, nothing else.

Hinglish: {text}
English:"""
        
        try:
            result = self.llm.generate(prompt, temperature=0.1)
            translated = result.strip()
            print(f"[RAG] Hinglish translated: '{text}' -> '{translated}'")
            return translated if translated else text
        except Exception as e:
            print(f"[RAG Error] Hinglish translation failed: {e}")
            return text
    
    def translate_to_hinglish(self, text: str) -> str:
        """
        Translate English text to Hinglish (romanized Hindi in English letters) using Ollama.
        Example output: "Murder ki saza maut ya umar kaid hai. IPC Section 302..."
        """
        if not self.llm.enabled:
            return text  # Return original if LLM not available
        
        prompt = f"""Convert this English text to Hinglish (Hindi written in English/Roman letters, NOT Devanagari script).
Use common Hindi words written in English letters. Keep legal terms and section numbers in English.
Only output the Hinglish translation, nothing else.

English: {text}
Hinglish:"""
        
        try:
            result = self.llm.generate(prompt, temperature=0.3)
            translated = result.strip()
            print(f"[RAG] Translated to Hinglish")
            return translated if translated else text
        except Exception as e:
            print(f"[RAG Error] Hinglish translation failed: {e}")
            return text
    
    def translate_to_hindi(self, text: str) -> str:
        """
        Translate English text to Hindi using Google Translator.
        """
        try:
            # Split into smaller chunks to avoid length limits
            # Translate line by line for better results
            lines = text.split('\n')
            translated_lines = []
            
            translator = GoogleTranslator(source='en', target='hi')
            
            for line in lines:
                if line.strip():
                    # Skip markdown headers and formatting for better translation
                    if line.startswith('#') or line.startswith('**') or line.startswith('>'):
                        # Translate content inside markdown
                        translated = translator.translate(line)
                        translated_lines.append(translated if translated else line)
                    else:
                        translated = translator.translate(line)
                        translated_lines.append(translated if translated else line)
                else:
                    translated_lines.append(line)
            
            return '\n'.join(translated_lines)
        except Exception as e:
            print(f"[Translation Error] {e}")
            return text  # Return original if translation fails

    def generate_answer(self, query: str, context: dict) -> str:
        """
        Generate answer based on retrieved context.
        Uses LLM (Ollama) when available, falls back to template otherwise.
        Automatically detects query language and responds in the same language.
        """
        # Detect query language
        query_lang = self.detect_language(query)
        print(f"[RAG] Detected query language: {query_lang}")
        
        # Debug: Log what context we received
        for key, value in context.items():
            print(f"[RAG] Context '{key}': {len(value)} results")
        
        # Check if we have any context
        if not any(context.values()):
            no_result_msg = "I could not find any matching information in the selected databases (IPC, BNS, Mapping, or Case Law). Try adjusting your filters or rephrasing your query."
            if query_lang == 'hinglish':
                return self.translate_to_hinglish(no_result_msg)
            elif query_lang == 'hi':
                return self.translate_to_hindi(no_result_msg)
            return no_result_msg
        
        # Try LLM-powered response first
        if self.llm.enabled:
            print("[RAG] Using Ollama LLM for response generation...")
            
            # For Hinglish, tell LLM to output directly in Hinglish (faster - no translation needed)
            if query_lang == 'hinglish':
                print("[RAG] Generating response directly in Hinglish...")
                answer = self.llm.generate_legal_answer(query, context, response_language='hinglish')
                # No translation needed - LLM outputs Hinglish directly!
            elif query_lang == 'hi':
                answer = self.llm.generate_legal_answer(query, context)
                print("[RAG] Translating response to Hindi (Devanagari)...")
                answer = self.translate_to_hindi(answer)
            else:
                # English - no translation needed
                answer = self.llm.generate_legal_answer(query, context)
            
            return answer
        
        # Fallback: Template-based response
        print("[RAG] LLM not available, using template response...")
        response_parts = []
        
        response_parts.append(f"### Analysis for: *{query}*\n")
        
        # Quick Mapping: Show instant IPC ↔ BNS conversion if found
        if context.get("quick_mapping"):
            qm = context["quick_mapping"][0]
            response_parts.append(f"**⚡ Quick Reference:**")
            if "ipc" in qm and "bns" in qm:
                response_parts.append(f"- **IPC Section {qm['ipc']}** → **BNS Section {qm['bns']}**")
                response_parts.append(f"- Category: {qm.get('category', 'Unknown')}\n")
        
        # Mapping Logic: If mapping found, highlight the transition
        if context.get("mapping"):
            top_map = context["mapping"][0]
            bns_sec = top_map["metadata"]["bns_section"]
            ipc_sec = top_map["metadata"]["ipc_section"]
            subject = top_map["metadata"]["subject"]
            
            response_parts.append(f"**Legal Transition:**")
            response_parts.append(f"The relevant law has transitioned from **IPC Section {ipc_sec}** to **BNS Section {bns_sec}**.")
            response_parts.append(f"**Subject:** {subject}")
            response_parts.append(f"**Changes:** {top_map['metadata']['summary']}\n")

        # BNS Logic
        if context["bns"]:
            top_bns = context["bns"][0]
            response_parts.append(f"**New Law (BNS):**")
            response_parts.append(f"Section {top_bns['metadata']['section_number']}: {top_bns['metadata']['section_title']}")
            response_parts.append(f"> {top_bns['text'][:300]}...\n") # Preview

        # IPC Logic
        if context["ipc"]:
            top_ipc = context["ipc"][0]
            response_parts.append(f"**Old Law (IPC):**")
            response_parts.append(f"Section {top_ipc['metadata']['section_number']}: {top_ipc['metadata']['section_title']}")
        
        # Case Law Logic - Show relevant precedents
        if context.get("case_law"):
            response_parts.append(f"\n**Relevant Case Law:**")
            for i, case in enumerate(context["case_law"][:3]):  # Top 3 cases
                meta = case["metadata"]
                case_title = meta.get("case_title", "Unknown Case")
                case_date = meta.get("case_date", "Unknown Date")
                year = meta.get("year", "")
                response_parts.append(f"- **{case_title}** ({case_date})")
                # Add brief preview of case content
                preview = case["text"][:150].replace("\n", " ")
                response_parts.append(f"  > {preview}...")
        
        answer = "\n".join(response_parts)
        
        # Translate response based on query language
        if query_lang == 'hinglish':
            print("[RAG] Translating response to Hinglish (romanized Hindi)...")
            answer = self.translate_to_hinglish(answer)
        elif query_lang == 'hi':
            print("[RAG] Translating response to Hindi (Devanagari)...")
            answer = self.translate_to_hindi(answer)
        
        return answer
