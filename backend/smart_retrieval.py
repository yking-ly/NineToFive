"""
Smart Retrieval Logic - The "Router" System

This module implements Phase B of the refined Smart Legal RAG System:
1. Input Analysis (The "Interceptor") - Detects Section/Article queries
2. Fast Path - Instant JSON lookups for specific provisions
3. Deep Path - Semantic search with query expansion
4. Strict Answer Generation - Grounded in retrieved context
"""

import re
import json
import os
from typing import List, Dict, Any, Optional, Tuple

import core


# ============================================================================
# PHASE B: SMART RETRIEVAL LOGIC
# ============================================================================

class QueryRouter:
    """
    Routes user queries through Fast Path or Deep Path based on intent detection.
    """
    
    def __init__(self):
        self.uploads_db = self.load_uploads_db()
    
    def load_uploads_db(self) -> Dict:
        """Load the JSON Map (Fast Brain)"""
        DB_FILE = "uploads_db.json"
        
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                return json.loads(content) if content else {"documents": {}}
        return {"documents": {}}
    
    def reload_db(self):
        """Reload the database (call after new ingestion)"""
        self.uploads_db = self.load_uploads_db()
    
    
    # ========================================================================
    # STEP 1: INPUT ANALYSIS (The Interceptor)
    # ========================================================================
    
    def detect_section_query(self, query: str) -> Optional[Dict[str, str]]:
        """
        Detects if query is asking about a specific Section/Article.
        
        Patterns:
            - "Section 304"
            - "Article 21"
            - "Sec 103"
            - "What is Section 304?"
            - "Tell me about Article 21"
        
        Returns:
            {
                "type": "section" | "article",
                "id": "304",
                "original_query": "..."
            }
            or None if no match
        """
        
        # Comprehensive regex patterns
        patterns = [
            r'(?:Section|Sec\.?)\s*(\d+[A-Z]*)',
            r'(?:Article|Art\.?)\s*(\d+[A-Z]*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                section_id = match.group(1).strip().upper()
                
                # Determine type
                query_type = "article" if "article" in pattern.lower() else "section"
                
                return {
                    "type": query_type,
                    "id": section_id,
                    "original_query": query
                }
        
        return None
    
    
    # ========================================================================
    # STEP 2: FAST PATH (Instant JSON Lookup)
    # ========================================================================
    
    def fast_lookup(self, section_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Performs instant lookup in uploads_db.json.
        
        Latency: ~50ms (Zero AI usage)
        
        Returns:
            {
                "found": True,
                "section_id": "304",
                "title": "Snatching",
                "summary": "...",
                "severity": "Cognizable",
                "bailable": "No",
                "keywords": [...],
                "page": 112,
                "act": "BNS",
                "filename": "BNS_Act_2023.pdf",
                "chroma_uuid": "..."
            }
            or None if not found
        """
        
        section_id = section_info["id"]
        
        # Search across all documents
        for file_id, document in self.uploads_db.get("documents", {}).items():
            sections = document.get("sections", {})
            
            if section_id in sections:
                section_data = sections[section_id]
                
                return {
                    "found": True,
                    "section_id": section_id,
                    "title": section_data.get("title", ""),
                    "summary": section_data.get("summary", ""),
                    "severity": section_data.get("severity", "N/A"),
                    "bailable": section_data.get("bailable", "N/A"),
                    "keywords": section_data.get("keywords", []),
                    "page": section_data.get("page", 0),
                    "act": document.get("act", "UNKNOWN"),
                    "filename": document.get("filename", ""),
                    "chroma_uuid": section_data.get("chroma_uuid", ""),
                    "crime": section_data.get("crime", "")
                }
        
        return None
    
    
    def format_fast_response(self, lookup_result: Dict[str, Any], query: str) -> str:
        """
        Formats the fast lookup result into a user-friendly response.
        
        Returns markdown-formatted text suitable for display.
        """
        
        response = f"""### 📋 Section {lookup_result['section_id']}: {lookup_result['title']}

**Summary:** {lookup_result['summary']}

**Legal Details:**
- **Severity:** {lookup_result['severity']}
- **Bailable:** {lookup_result['bailable']}
- **Crime Category:** {lookup_result['crime']}

**Source:** {lookup_result['act']} (Page {lookup_result['page']})

**Related Keywords:** {', '.join(lookup_result['keywords'][:5])}

---

*This information was retrieved instantly from {lookup_result['filename']}*
"""
        
        return response.strip()
    
    
    # ========================================================================
    # STEP 3: DEEP PATH (Semantic Search with RAG)
    # ========================================================================
    
    def expand_query(self, query: str) -> List[str]:
        """
        Uses LLM to generate query expansions for better retrieval.
        
        Example:
            "stole phone" → ["theft", "snatching", "movable property", "stolen phone"]
        
        Returns: List of expanded queries (max 5)
        """
        
        prompt = f"""You are a legal search expert. Expand this user query into related legal terms and common phrases.

USER QUERY: "{query}"

TASK: Generate 5 alternative search phrases that capture the same intent using:
1. Legal terminology
2. Common slang/everyday language
3. Related concepts

Return ONLY a JSON array of strings. Example:
["term1", "term2", "term3", "term4", "term5"]

IMPORTANT: Return ONLY the JSON array, no explanations.
"""
        
        try:
            response = core.safe_llm_invoke(prompt, max_tokens=150, temperature=0.5)
            
            # Clean and parse
            response = response.replace("```json", "").replace("```", "").strip()
            expansions = json.loads(response)
            
            # Validate it's a list
            if isinstance(expansions, list):
                return [query] + expansions[:4]  # Original + 4 expansions
            
        except Exception as e:
            print(f"Query expansion failed: {e}")
        
        # Fallback: return original query
        return [query]
    
    
    def deep_search(
        self, 
        query: str, 
        n_results: int = 5,
        use_expansion: bool = True
    ) -> List[Tuple[Any, float]]:
        """
        Performs semantic search in Vector DB.
        
        Process:
            1. Query Expansion (if enabled)
            2. Search ChromaDB with expanded queries
            3. Deduplicate and rerank results
        
        Returns: List of (Document, score) tuples
        """
        
        from retrieval import retrieve_context
        
        # Optional query expansion
        if use_expansion:
            expanded_queries = self.expand_query(query)
            print(f"[DEEP SEARCH] Expanded to: {expanded_queries}")
        else:
            expanded_queries = [query]
        
        # Retrieve context using existing retrieval logic
        # The retrieve_context function already handles:
        # - Multi-query search
        # - Deduplication
        # - Reranking
        
        results = retrieve_context(
            query_text=query,
            n_results=n_results * 2,  # Get more initially for better reranking
            language='en'
        )
        
        return results[:n_results]
    
    
    def generate_grounded_answer(
        self,
        query: str,
        context_docs: List[Tuple[Any, float]],
        chat_history: List[Dict] = []
    ) -> str:
        """
        Generates answer strictly grounded in retrieved context.
        
        System Prompt: Enforces citation and anti-hallucination rules.
        """
        
        # Build context string
        context_parts = []
        for i, (doc, score) in enumerate(context_docs, 1):
            metadata = doc.metadata
            section_id = metadata.get('section_id', 'UNKNOWN')
            act = metadata.get('act', 'UNKNOWN')
            
            context_parts.append(f"""
[SOURCE {i}]
Section: {section_id} ({act})
Content: {doc.page_content[:800]}
---""")
        
        context_str = "\n".join(context_parts)
        
        # Build history context
        history_str = ""
        if chat_history:
            recent_history = chat_history[-4:]  # Last 2 exchanges
            for msg in recent_history:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                history_str += f"{role.upper()}: {content}\n"
        
        # Anti-hallucination prompt
        system_prompt = f"""You are Kira, a legal AI assistant. Answer the user's question using ONLY the provided context.

CRITICAL RULES:
1. **CITE EXPLICITLY**: Always mention Section numbers and Act names (e.g., "Section 304 of BNS")
2. **NO HALLUCINATION**: If the context doesn't contain the answer, say "I don't have information about that in the uploaded documents."
3. **DISTINGUISH**: Clearly separate "Definition" vs "Punishment" when both are present
4. **NATURAL TONE**: Be conversational but precise

CONTEXT:
{context_str}

PREVIOUS CONVERSATION:
{history_str}

USER QUESTION: {query}

ANSWER (use markdown formatting):"""

        try:
            # Stream response
            response_chunks = []
            for chunk in core.safe_llm_stream(system_prompt, max_tokens=800, temperature=0.3):
                response_chunks.append(chunk)
            
            return "".join(response_chunks)
            
        except Exception as e:
            print(f"Answer generation failed: {e}")
            return "I encountered an error while processing your request. Please try again."
    
    
    # ========================================================================
    # MASTER ROUTING LOGIC
    # ========================================================================
    
    def route_query(
        self,
        query: str,
        chat_history: List[Dict] = [],
        status_callback=None
    ) -> Dict[str, Any]:
        """
        Master routing logic that decides Fast Path vs Deep Path.
        
        Returns:
            {
                "path": "fast" | "deep",
                "response": str,
                "sources": List[Dict],
                "latency_ms": int
            }
        """
        
        import time
        start_time = time.time()
        
        def send_status(msg: str):
            if status_callback:
                status_callback(msg)
            print(f"[ROUTER] {msg}")
        
        # Reload DB to ensure latest data
        self.reload_db()
        
        # STEP 1: Check for Section/Article pattern
        send_status("🔍 Analyzing query intent...")
        section_info = self.detect_section_query(query)
        
        if section_info:
            # FAST PATH
            send_status(f"⚡ Detected {section_info['type']} query: {section_info['id']}")
            send_status("📋 Performing instant lookup...")
            
            lookup_result = self.fast_lookup(section_info)
            
            if lookup_result:
                response = self.format_fast_response(lookup_result, query)
                latency = int((time.time() - start_time) * 1000)
                
                send_status(f"✅ Found in {latency}ms (Fast Path)")
                
                return {
                    "path": "fast",
                    "response": response,
                    "sources": [lookup_result],
                    "latency_ms": latency,
                    "section_id": section_info['id']
                }
            else:
                send_status(f"⚠ Section {section_info['id']} not found in database")
                # Fall through to deep path
        
        # DEEP PATH
        send_status("🧠 Initiating semantic search...")
        send_status("📊 Retrieving relevant context...")
        
        context_docs = self.deep_search(query, n_results=5, use_expansion=True)
        
        if not context_docs:
            return {
                "path": "deep",
                "response": "I couldn't find relevant information in the uploaded documents. Please try rephrasing your question or upload relevant legal documents.",
                "sources": [],
                "latency_ms": int((time.time() - start_time) * 1000)
            }
        
        send_status(f"✓ Retrieved {len(context_docs)} relevant sections")
        send_status("🤖 Generating grounded answer...")
        
        response = self.generate_grounded_answer(query, context_docs, chat_history)
        
        # Extract sources
        sources = []
        for doc, score in context_docs:
            metadata = doc.metadata
            sources.append({
                "section_id": metadata.get('section_id', 'UNKNOWN'),
                "act": metadata.get('act', 'UNKNOWN'),
                "title": metadata.get('title', ''),
                "relevance_score": float(score)
            })
        
        latency = int((time.time() - start_time) * 1000)
        send_status(f"✅ Complete in {latency}ms (Deep Path)")
        
        return {
            "path": "deep",
            "response": response,
            "sources": sources,
            "latency_ms": latency
        }


# ============================================================================
# CONVENIENCE WRAPPER
# ============================================================================

# Global router instance
_router = None

def get_router() -> QueryRouter:
    """Get or create the global QueryRouter instance"""
    global _router
    if _router is None:
        _router = QueryRouter()
    return _router


def smart_query(
    query: str,
    chat_history: List[Dict] = [],
    status_callback=None
) -> Dict[str, Any]:
    """
    Convenience function for smart querying.
    
    Usage:
        result = smart_query("What is Section 304?")
        print(result['response'])
    """
    router = get_router()
    return router.route_query(query, chat_history, status_callback)
