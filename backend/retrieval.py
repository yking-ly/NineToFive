from sentence_transformers import CrossEncoder
import core
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from deep_translator import GoogleTranslator
import re
import json
import os
import smart_retrieval  # Import the smart retrieval router


# ============================================================================
# SMART RETRIEVAL HELPER FUNCTIONS
# ============================================================================

def load_uploads_db() -> List[Dict[str, Any]]:
    """Loads the uploads_db.json file."""
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend', 'uploads_db.json')
    if not os.path.exists(db_path):
        return []
    try:
        with open(db_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading uploads_db.json: {e}")
        return []

# User-defined Core Documents Priority List
# "refer(the summaries) from these first"
CORE_DOC_MAPPING = {
    'BSA': 'BSA',
    'BNS': 'BNS',
    'BNSS': 'BNSS',
    'IPC_BNS_MAPPING': 'IPC_BNS_Mapping',
    'IEA': 'IEA',
    'CRPC': 'CrPC',
    'IPC': 'IPC',
    'TC': 'TC',
    'TCOI': 'TCOI'
}

def search_uploads_index(query: str) -> List[Dict[str, Any]]:
    """
    Searches uploads_db.json for documents matching the query.
    PRIORITIZES Core Legal Documents specified by user.
    """
    db_data = load_uploads_db()
    matches = []
    
    query_upper = query.upper()
    query_terms = query.lower().split()
    
    # 1. Identify if query hits any Core Doc acronyms
    target_core_docs = []
    for acronym, filename_part in CORE_DOC_MAPPING.items():
        # strict word boundary check for acronyms to avoid partial matches
        if re.search(r'\b' + re.escape(acronym) + r'\b', query_upper):
            target_core_docs.append(filename_part.lower())
    
    for doc in db_data:
        filename = doc.get('filename', '').lower()
        summary = doc.get('summary', '').lower()
        
        score = 0
        
        # Priority 1: Core Document Match
        for core_target in target_core_docs:
            if core_target in filename:
                score += 100 # Massive boost for requested core docs
                break
        
        # Priority 2: Keyword Match
        for term in query_terms:
            if len(term) < 3: continue 
            if term in filename:
                score += 3
            if term in summary:
                score += 1
                
        if score > 0:
            doc['search_score'] = score
            matches.append(doc)
            
    # Sort by score
    matches.sort(key=lambda x: x.get('search_score', 0), reverse=True)
    return matches[:5] # Increase to top 5 to catch multiple core docs


# ============================================================================
# SMART RETRIEVAL HELPER FUNCTIONS
# ============================================================================

def extract_conversation_topics(chat_history: List[dict]) -> List[str]:
    """
    Extracts key topics from conversation history for chained context retrieval.
    Returns a list of relevant search queries based on previous exchanges.
    """
    if not chat_history or len(chat_history) < 2:
        return []
    
    topics = []
    
    # Extract from last 4-6 messages
    recent_messages = chat_history[-6:]
    
    for msg in recent_messages:
        if msg.get('role') == 'user':
            content = msg.get('content', '')
            # Extract legal terms, section numbers, acts
            # Section numbers (e.g., "Section 302", "Article 21")
            sections = re.findall(r'(?:section|article|clause|rule)\s+\d+[a-z]?', content, re.IGNORECASE)
            topics.extend(sections)
            
            # Legal acts mentioned
            acts = re.findall(r'\b(?:IPC|BNS|CrPC|BNSS|IEA|BSA|IT Act|Constitution)\b', content, re.IGNORECASE)
            topics.extend(acts)
            
            # Extract key nouns (simplified - take capitalized words that might be legal terms)
            keywords = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
            topics.extend(keywords[:3])  # Limit to 3 keywords per message
    
    # Remove duplicates while preserving order
    seen = set()
    unique_topics = []
    for topic in topics:
        topic_lower = topic.lower()
        if topic_lower not in seen:
            seen.add(topic_lower)
            unique_topics.append(topic)
    
    return unique_topics[:5]  # Return top 5 topics

def analyze_query_complexity(query: str) -> dict:
    """
    Analyzes query to determine its complexity and type.
    Returns: {'type': str, 'confidence': float, 'keywords': list}
    Types: 'simple', 'complex', 'comparative', 'procedural'
    """
    query_lower = query.lower()
    
    # Complexity indicators
    complex_indicators = [
        'explain', 'analyze', 'compare', 'contrast', 'difference', 'between',
        'why', 'how does', 'what are the implications', 'discuss', 'elaborate',
        'relationship', 'impact', 'effect', 'consequence', 'versus', 'vs'
    ]
    
    procedural_indicators = [
        'procedure', 'process', 'steps', 'how to', 'method', 'way to',
        'file', 'apply', 'register', 'obtain', 'submit'
    ]
    
    comparative_indicators = [
        'compare', 'contrast', 'difference', 'between', 'versus', 'vs',
        'similar', 'different', 'both', 'either'
    ]
    
    simple_indicators = [
        'what is', 'define', 'who is', 'when', 'where', 'which section',
        'section', 'article', 'clause', 'punishment', 'penalty'
    ]
    
    # Count indicators
    complex_count = sum(1 for ind in complex_indicators if ind in query_lower)
    procedural_count = sum(1 for ind in procedural_indicators if ind in query_lower)
    comparative_count = sum(1 for ind in comparative_indicators if ind in query_lower)
    simple_count = sum(1 for ind in simple_indicators if ind in query_lower)
    
    # Question length (longer questions tend to be more complex)
    word_count = len(query.split())
    
    # Determine type
    if comparative_count >= 2 or 'compare' in query_lower:
        query_type = 'comparative'
        confidence = min(0.9, 0.6 + comparative_count * 0.1)
    elif complex_count >= 2 or word_count > 15:
        query_type = 'complex'
        confidence = min(0.9, 0.5 + complex_count * 0.1 + (word_count - 10) * 0.02)
    elif procedural_count >= 1:
        query_type = 'procedural'
        confidence = min(0.9, 0.6 + procedural_count * 0.15)
    elif simple_count >= 1 and word_count < 10:
        query_type = 'simple'
        confidence = min(0.9, 0.7 + simple_count * 0.1)
    else:
        # Default based on length
        if word_count > 12:
            query_type = 'complex'
            confidence = 0.6
        else:
            query_type = 'simple'
            confidence = 0.5
    
    # Extract key legal terms
    legal_terms = re.findall(r'\b(?:section|article|clause|act|code|rule|regulation|amendment)\s+\d+[a-z]?\b', query_lower)
    
    return {
        'type': query_type,
        'confidence': confidence,
        'keywords': legal_terms,
        'word_count': word_count
    }

def determine_chunk_count(query_complexity: dict, category_tag: str = None) -> int:
    """
    Determines optimal number of chunks to retrieve based on query complexity.
    """
    base_counts = {
        'simple': 3,
        'complex': 6,
        'comparative': 8,
        'procedural': 5
    }
    
    chunk_count = base_counts.get(query_complexity['type'], 4)
    
    # Adjust based on confidence
    if query_complexity['confidence'] > 0.8:
        chunk_count += 1
    
    # If category tag is specified, we can be more focused
    if category_tag:
        chunk_count = max(3, chunk_count - 1)
    
    # Cap at reasonable limits
    return min(chunk_count, 10)

from flashrank import Ranker, RerankRequest

# Global reranker instance
_reranker = None

def get_reranker():
    global _reranker
    if _reranker is None:
        try:
            print("Loading FlashRank Reranker (ms-marco-MiniLM-L-12-v2)...")
            # FlashRank downloads the quantized model automatically (approx 40MB)
            _reranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir="model")
        except Exception as e:
            print(f"Failed to load FlashRank: {e}")
    return _reranker

def generate_query_expansions(query: str, query_complexity: dict) -> List[str]:
    """
    Generates expanded queries using Qwen for better retrieval coverage.
    """
    try:
        prompt = f"""<|im_start|>system
You are a legal research assistant. Generate 3 diverse search queries based on the user's query context.
Include legal synonyms, specific act sections (e.g., if user asks about murder, include 'BNS Section 103'), and technical terms.
Output ONLY the 3 queries, one per line.<|im_end|>
<|im_start|>user
Input Query: {query}<|im_end|>
<|im_start|>assistant
"""
        response = core.safe_llm_invoke(prompt, stop=["<|im_end|>"], max_tokens=100)
        expansions = [q.strip() for q in response.strip().split('\n') if q.strip()]
        
        # Fallback if LLM fails or returns empty
        if not expansions:
            raise ValueError("Empty LLM expansion")
            
        print(f"🤖 Qwen generated expansions: {expansions[:3]}")
        return expansions[:3]
        
    except Exception as e:
        print(f"Fallback to heuristic expansion: {e}")
        # FALLBACK to existing heuristic logic
        expansions = []
        query_lower = query.lower()
        if query_complexity['type'] == 'comparative':
            if ' and ' in query_lower:
                parts = query_lower.split(' and ')
                expansions.extend(parts[:2])
            elif ' vs ' in query_lower:
                parts = re.split(r'\s+(?:vs|versus)\s+', query_lower)
                expansions.extend(parts[:2])
        if query_complexity['type'] == 'complex':
            words = query.split()
            if len(words) > 5:
                mid = len(words) // 2
                expansions.append(' '.join(words[:mid]))
                expansions.append(' '.join(words[mid:]))
        if query_complexity['keywords']:
            for term in query_complexity['keywords'][:2]:
                expansions.append(term)
        return expansions[:3]

def rerank_results(query: str, results: List[tuple], top_k: int = 5) -> List[tuple]:
    """
    Reranks the retrieved chunks using FlashRank (Lightweight/Quantized).
    """
    reranker = get_reranker()
    if not reranker or not results:
        print("⚠️ FlashRank not available, returning vector results.")
        return results[:top_k]
    
    unique_docs = deduplicate_results(results)
    if not unique_docs:
        return []
        
    # Prepare inputs for FlashRank
    # FlashRank expects: [{"id": 1, "text": "content", "meta": {...}}, ...]
    passages = []
    doc_map = {} # map id back to doc object
    
    for i, (doc, vector_score) in enumerate(unique_docs):
        doc_id = i
        passages.append({
            "id": doc_id,
            "text": doc.page_content,
            "meta": doc.metadata if doc.metadata else {}
        })
        doc_map[doc_id] = doc

    try:
        print(f"⚡ FlashRank Reranking {len(passages)} chunks...")
        
        rerank_request = RerankRequest(query=query, passages=passages)
        ranked_results = reranker.rerank(rerank_request)
        
        # Parse output
        # Output is list of dicts: [{'id': 1, 'score': 0.9, ...}, ...]
        
        final_results = []
        for item in ranked_results:
            doc_id = item['id']
            score = item['score']
            if doc_id in doc_map:
                final_results.append((doc_map[doc_id], score))
            
        # Sort by score DESCENDING (FlashRank returns 0.0 to 1.0, higher is better)
        # (Though FlashRank usually returns them sorted, we ensure it)
        final_results.sort(key=lambda x: x[1], reverse=True)
        
        if final_results:
             print(f"   Top FlashRank score: {final_results[0][1]:.4f}")
             
        return final_results[:top_k]
        
    except Exception as e:
        print(f"FlashRank failed: {e}")
        return results[:top_k]

def deduplicate_results(results: List[tuple]) -> List[tuple]:
    """
    Removes duplicate or highly similar chunks from results.
    Returns unique results based on content similarity.
    """
    if not results:
        return []
    
    unique_results = []
    seen_contents = set()
    
    for doc, score in results:
        # Create a hash of the ALL content to avoid false positives on boilerplate headers
        content_hash = hash(doc.page_content)
        
        if content_hash not in seen_contents:
            seen_contents.add(content_hash)
            unique_results.append((doc, score))
    
    return unique_results

def get_relevance_threshold(query_complexity: dict) -> float:
    """
    Determines relevance threshold based on query complexity.
    Lower threshold = more strict filtering
    """
    thresholds = {
        'simple': 1.2,      # Strict - we want exact matches
        'complex': 1.8,     # More lenient - need broader context
        'comparative': 2.0,  # Very lenient - need diverse sources
        'procedural': 1.5   # Moderate - need step-by-step info
    }
    
    base_threshold = thresholds.get(query_complexity['type'], 1.5)
    
    # Adjust based on confidence
    if query_complexity['confidence'] < 0.6:
        base_threshold += 0.3  # Be more lenient if uncertain
    
    return base_threshold

def check_context_relevance(query: str, context: str, query_complexity: dict) -> dict:
    """
    Analyzes if the retrieved context actually answers the query.
    Returns: {'is_relevant': bool, 'confidence': float, 'missing_keywords': list}
    """
    query_lower = query.lower()
    context_lower = context.lower()
    
    # Extract key query terms (nouns, legal terms, numbers)
    query_keywords = set()
    
    # Legal-specific patterns
    legal_patterns = [
        r'section\s+\d+[a-z]?',
        r'article\s+\d+',
        r'chapter\s+\d+',
        r'ipc|bns|crpc|bnss|iea|bsa',
        r'\d{4}',  # Years
    ]
    
    for pattern in legal_patterns:
        matches = re.findall(pattern, query_lower)
        query_keywords.update(matches)
    
    # Extract important nouns (simplified - words > 4 chars, not common words)
    common_words = {'what', 'when', 'where', 'which', 'about', 'under', 'does', 'mean', 'explain', 'tell', 'define'}
    words = re.findall(r'\b[a-z]{4,}\b', query_lower)
    query_keywords.update([w for w in words if w not in common_words])
    
    # Check keyword coverage
    found_keywords = set()
    missing_keywords = set()
    
    for keyword in query_keywords:
        if keyword in context_lower:
            found_keywords.add(keyword)
        else:
            missing_keywords.add(keyword)
    
    # Calculate relevance score
    if not query_keywords:
        return {'is_relevant': True, 'confidence': 0.5, 'missing_keywords': []}
    
    coverage = len(found_keywords) / len(query_keywords) if query_keywords else 0
    
    # Thresholds based on query type
    min_coverage = {
        'simple': 0.7,      # Need 70% keyword match for simple queries
        'complex': 0.5,     # Need 50% for complex (broader context acceptable)
        'comparative': 0.4,  # Need 40% for comparative (diverse sources)
        'procedural': 0.6   # Need 60% for procedural (step-by-step)
    }
    
    required_coverage = min_coverage.get(query_complexity['type'], 0.5)
    is_relevant = coverage >= required_coverage
    
    return {
        'is_relevant': is_relevant,
        'confidence': coverage,
        'missing_keywords': list(missing_keywords)
    }

def verify_legal_citations(response: str, context: str) -> dict:
    """
    Verifies that all legal citations in the response actually exist in the context.
    Detects hallucinated provisions to prevent misinformation.
    Returns: {'valid': bool, 'violations': list, 'warning': str}
    """
    violations = []
    
    # Patterns for legal citations
    article_pattern = r'Article\s+\d+[A-Za-z]?(?:\([^)]+\))?'
    section_pattern = r'Section\s+\d+[A-Za-z]?(?:\([^)]+\))?'
    chapter_pattern = r'Chapter\s+\d+[A-Za-z]?'
    
    # Extract citations from response and context
    response_articles = set(re.findall(article_pattern, response, re.IGNORECASE))
    response_sections = set(re.findall(section_pattern, response, re.IGNORECASE))
    response_chapters = set(re.findall(chapter_pattern, response, re.IGNORECASE))
    
    context_articles = set(re.findall(article_pattern, context, re.IGNORECASE))
    context_sections = set(re.findall(section_pattern, context, re.IGNORECASE))
    context_chapters = set(re.findall(chapter_pattern, context, re.IGNORECASE))
    
    # Check for hallucinated citations
    for article in response_articles:
        # Normalize for comparison (case-insensitive)
        if not any(article.lower() == ctx.lower() for ctx in context_articles):
            violations.append(f"❌ HALLUCINATED: {article} cited but not found in context")
    
    for section in response_sections:
        if not any(section.lower() == ctx.lower() for ctx in context_sections):
            violations.append(f"❌ HALLUCINATED: {section} cited but not found in context")
    
    for chapter in response_chapters:
        if not any(chapter.lower() == ctx.lower() for ctx in context_chapters):
            violations.append(f"❌ HALLUCINATED: {chapter} cited but not found in context")
    
    is_valid = len(violations) == 0
    warning = ""
    
    if not is_valid:
        warning = "\n\n⚠️ WARNING: This response may contain inaccurate legal citations. Please verify independently."
    
    return {
        'valid': is_valid,
        'violations': violations,
        'warning': warning,
        'stats': {
            'articles_cited': len(response_articles),
            'sections_cited': len(response_sections),
            'chapters_cited': len(response_chapters)
        }
    }



def retrieve_context(query_text: str, n_results: int = 50, language: str = 'en', status_callback=None, persona: str = 'default', query_complexity: dict = None) -> List[tuple]:
    """
    Reusable function to retrieve and rerank context for ANY purpose (Chat or Summary).
    Encapsulates: 
    - Translation
    - Index Search (uploads_db.json)
    - Progressive Deepening
    - Query Expansion
    - FlashRank Reranking
    - Adaptive Deep Search
    
    Returns: List of (Document, score) tuples.
    """
    def send_status(msg):
        if status_callback:
            status_callback(msg)

    # Note: query_text should already be analyzed for complexity if possible, 
    # but we handle basic analysis if not provided.

    effective_query = query_text
    
    # 0. Translation (if needed for retrieval) already assumed done by caller or here?
    # For reusability, let's assume caller might give us Hindi, but we prefer English.
    # But usually App handles input translation. 
    # We will assume effective_query is what we want to search with.
    
    # 1. Smart Query Analysis (if not passed)
    if not query_complexity:
        query_complexity = analyze_query_complexity(effective_query)
        
    print(f"Retrieving context for: '{effective_query[:50]}...' (Complexity: {query_complexity['type']}, n={n_results})")
    
    dbs = core.get_dbs()
    all_results = []
    skip_general_search = False
    
    # STRATEGY 0: EXACT SECTION LOOKUP (The "Map" Strategy)
    # Fixes hallucinations by prioritizing curated legal facts
    try:
        sections_index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sections_index.json')
        if os.path.exists(sections_index_path):
            with open(sections_index_path, 'r', encoding='utf-8') as f:
                sections_map = json.load(f)
                
            q_lower = effective_query.lower()
            for entry in sections_map:
                # Check all keywords
                for kw in entry.get('keywords', []):
                    if kw.lower() in q_lower:
                        print(f"🌟 EXACT MATCH FOUND: {entry['section']} - {entry['title']}")
                        send_status(f"🎯 Verified Match: {entry['section']} ({entry['act']})")
                        
                        # Create a "Gold Standard" document
                        try:
                            from langchain_core.documents import Document
                        except ImportError:
                            from langchain.docstore.document import Document
                            
                        exact_doc = Document(
                            page_content=f"**OFFICIAL LEGAL RECORD**:\n**Act**: {entry['act']}\n**Section**: {entry['section']}\n**Title**: {entry['title']}\n**Text**: {entry['content']}",
                            metadata={'source': 'Simulated_Legal_Index', 'type': 'exact_match', 'section': entry['section'], 'confidence': 1.0}
                        )
                        # Append with unbeatable score (0.0 is best distance, or negative to force top?)
                        # We use score 0.00001 to ensure it survives reranking/sorting
                        all_results.append((exact_doc, 0.0)) 
    except Exception as e:
        print(f"Section Index Error: {e}")

    # STRATEGY 0.5: STRUCTURED INDEX RETRIEVAL
    try:
        matched_docs = search_uploads_index(effective_query)
        if matched_docs:
            print(f"📂 Index Search: Found {len(matched_docs)} specific documents")
            
            # Check for CORE DOCS
            found_core_docs = []
            for doc in matched_docs:
                fname_upper = doc.get('filename', '').upper()
                if any(c_acro in fname_upper for c_acro in CORE_DOC_MAPPING.keys()):
                    found_core_docs.append(doc.get('filename'))
            
            if found_core_docs:
                print(f"🌟 CORE DOCS IDENTIFIED: {found_core_docs}")
                skip_general_search = True

            # Collect target filenames
            target_filenames = [d.get('filename') for d in matched_docs if d.get('filename')]

            # 1. INJECT SUMMARIES
            for doc in matched_docs:
                summary_text = doc.get('summary')
                filename = doc.get('filename', 'Unknown')
                if summary_text:
                    try:
                        from langchain_core.documents import Document
                    except ImportError:
                        from langchain.docstore.document import Document
                        
                    s_doc = Document(
                        page_content=f"**DOCUMENT SUMMARY for {filename}**:\n{summary_text}", 
                        metadata={'source': filename, 'type': 'summary', 'filename': filename}
                    )
                    all_results.append((s_doc, 0.0001))

            # 2. PERFORM FILTERED VECTOR SEARCH on these specific documents
            if target_filenames:
                def search_filtered(db):
                    results = []
                    if len(target_filenames) == 1:
                         f_filter = {'filename': target_filenames[0]}
                    else:
                         f_filter = {'filename': {'$in': target_filenames}}
                    try:
                        return db.similarity_search_with_score(effective_query, k=10, filter=f_filter)
                    except Exception:
                        return []

                with ThreadPoolExecutor(max_workers=core.NUM_SHARDS) as executor:
                    futures = [executor.submit(search_filtered, db) for db in dbs]
                    for future in as_completed(futures):
                        try:
                            res = future.result()
                            if res:
                                # Boost core docs
                                boosted_res = [(doc, max(score - 0.5, 0.001)) for doc, score in res]
                                all_results.extend(boosted_res)
                        except Exception:
                            pass
    except Exception as e:
        print(f"Index Retrieval Error: {e}")

    # PROGRESSIVE DEEPENING
    initial_k = n_results
    max_k = 20
    current_k = initial_k
    search_depth_level = 1
    max_depth_levels = 3
    
    # Strategy 1: Direct similarity search
    def search_shard(db, k):
        return db.similarity_search_with_score(effective_query, k=k)
    
    # Level 1: Initial direct search
    if not skip_general_search:
        # send_status(f"🔍 Finding top {n_results} chunks...") # Caller might send status
        with ThreadPoolExecutor(max_workers=core.NUM_SHARDS) as executor:
            futures = [executor.submit(search_shard, db, current_k) for db in dbs]
            for future in as_completed(futures):
                try:
                    all_results.extend(future.result())
                except Exception:
                    pass
    
    # Check if we need to dig deeper
    needs_deepening = False
    if all_results:
        best_score = min(score for _, score in all_results)
        chunk_count = sum(1 for r in all_results if r[1] > 0.0002)
        
        if skip_general_search and chunk_count < 3:
            needs_deepening = True
            skip_general_search = False
        elif best_score > 3.0:
            needs_deepening = True
    else:
        needs_deepening = True
        skip_general_search = False
    
    if needs_deepening:
        # send_status("🔎 Deepening search...")
        while needs_deepening and search_depth_level < max_depth_levels:
            search_depth_level += 1
            current_k = min(current_k * 2, max_k)
            
            # Additional search
            deeper_results = []
            with ThreadPoolExecutor(max_workers=core.NUM_SHARDS) as executor:
                futures = [executor.submit(search_shard, db, current_k) for db in dbs]
                for future in as_completed(futures):
                    try:
                        deeper_results.extend(future.result())
                    except Exception:
                        pass
            
            all_results.extend(deeper_results)
            if deeper_results:
                new_best_score = min(score for _, score in deeper_results)
                if new_best_score < 2.5:
                    break
            else:
                break
    
    # Strategy 2: Query Expansion
    # NOTE: For Summary pipeline, we might skip expansion if it's already an entity-based query.
    # But if query_complexity says 'complex', we do it.
    if query_complexity['type'] in ['complex', 'comparative'] or persona != 'kira':
        # send_status("🔄 Expanding queries...")
        expanded_queries = generate_query_expansions(effective_query, query_complexity)
        for exp_query in expanded_queries:
            with ThreadPoolExecutor(max_workers=core.NUM_SHARDS) as executor:
                futures = [executor.submit(lambda db: db.similarity_search_with_score(exp_query, k=min(current_k, 5)), db) for db in dbs]
                for future in as_completed(futures):
                    try:
                        all_results.extend(future.result())
                    except Exception:
                        pass

    # Remove duplicates
    all_results = deduplicate_results(all_results)
    
    # PHASE 2: RERANKING
    # Use Cross-Encoder to find the most relevant chunks from the top 50
    # send_status(f"⚡ Reranking {len(all_results)} results...")
    top_results = rerank_results(effective_query, all_results, top_k=5)
    
    if not top_results:
        return []

    # INTELLIGENT FEEDBACK LOOP: Check relevance
    context_texts = [doc.page_content for doc, _ in top_results]
    initial_context = "\n\n---\n\n".join(context_texts)
    
    # send_status("🧠 Checking context relevance...")
    relevance_check = check_context_relevance(effective_query, initial_context, query_complexity)
    
    # TRIGGER ADAPTIVE DEEP SEARCH
    if not relevance_check['is_relevant'] and relevance_check['missing_keywords']:
        send_status("🔎 Context incomplete. Triggering adaptive deep search...")
        print(f"🔎 Triggering adaptive deep search for missing: {relevance_check['missing_keywords'][:3]}")
        
        adaptive_queries = []
        for keyword in relevance_check['missing_keywords'][:3]:
            adaptive_queries.append(f"{keyword} {effective_query}")
            adaptive_queries.append(keyword)
        
        broader_query_terms = effective_query.split()
        if len(broader_query_terms) > 3:
            adaptive_queries.append(" ".join(broader_query_terms[:3]))
            adaptive_queries.append(" ".join(broader_query_terms[-3:]))
        
        adaptive_results = []
        for adapt_query in adaptive_queries:
            with ThreadPoolExecutor(max_workers=core.NUM_SHARDS) as executor:
                futures = [executor.submit(lambda db: db.similarity_search_with_score(adapt_query, k=5), db) for db in dbs]
                for future in as_completed(futures):
                    try:
                        adaptive_results.extend(future.result())
                    except Exception:
                        pass
        
        if adaptive_results:
            all_results.extend(adaptive_results)
            all_results = deduplicate_results(all_results)
            
            # send_status("⚖️ Re-ranking new findings...")
            top_results = rerank_results(effective_query, all_results, top_k=7)
    
    return top_results

def query_docs(query_text: str, chat_history: List[dict] = [], n_results: int = 3, language: str = 'en', category_tag: str = None, persona: str = 'default', status_callback=None):
    """
    Queries valid vector DBs (Persistent) + Answer Caching.
    (Wrapper around retrieve_context with LLM generation)
    """
    def send_status(msg):
        if status_callback:
            status_callback(msg)
            
    try:
        # Tag mapping for full names
        tag_mapping = {
            'ipc': 'Indian Penal Code (IPC)',
            'bns': 'Bharatiya Nyaya Sanhita (BNS)',
            'crpc': 'Criminal Procedure Code (CrPC)',
            'bnss': 'Bharatiya Nagarik Suraksha Sanhita (BNSS)',
            'iea': 'Indian Evidence Act (IEA)',
            'bsa': 'Bharatiya Sakshya Adhiniyam (BSA)',
        }
        
        send_status("🧠 Analyzing query complexity...")
        
        # Adjust n_results for specific personas
        skip_retrieval = False
        if persona == 'kira':
            try:
                import kira_processor
                
                # 1. Intent Analysis & Query Rewriting
                intent = kira_processor.detect_intent(query_text)
                print(f"Kira Intent: {intent}")
                
                if intent == 'chit_chat':
                    # Skip heavy retrieval for simple greetings
                    n_results = 0
                    skip_retrieval = True
                    effective_query = query_text # Don't rewrite chit-chat
                else:
                    # Contextual Rewriting
                    effective_query = kira_processor.build_kira_context(chat_history, query_text)
                    print(f"Kira Contextual Rewrite: '{query_text}' -> '{effective_query}'")
                    n_results = 3 # Voice Users can't digest more than 3 references
                    skip_retrieval = False
            except ImportError:
                print("Kira Processor not found, falling back to default.")
                n_results = max(n_results, 6)
                effective_query = query_text
                skip_retrieval = False
        else:
            print("Chat Mode: Deep search enabled with Context.")
            n_results = 15

        
        
        # 0. Handle Query Translation (Auto -> EN for retrieval)
        # We always process internally in English to use the English-optimized LLM and DB.
        if persona != 'kira' or not skip_retrieval:
            # Only translate/process if we are actually searching
            if persona != 'kira':
                 # For non-kira, query isn't rewritten yet, so sync it
                 effective_query = query_text
            
            # If a category tag is selected, prepend it to help focus the search
            if category_tag and category_tag in tag_mapping:
                category_name = tag_mapping[category_tag]
                effective_query = f"{category_name}: {effective_query}"
                print(f"Query refined with tag '{category_tag}': {effective_query}")
            
            # Translate input to English if it's in Hindi (both 'hi' and 'hi-romanized' might have Hindi input)
            if language in ['hi', 'hi-romanized']:
                try:
                    send_status("🌐 Translating query to English...")
                    # Translating query to English for retrieval
                    translator = GoogleTranslator(source='auto', target='en')
                    translated_query = translator.translate(effective_query)
                    print(f"Translated input query: '{query_text}' -> '{translated_query}'")
                    effective_query = translated_query
                    needs_input_translation = True
                except Exception as e:
                    print(f"Query translation failed: {e}")
                    # Fallback to original
                    pass

        # 1. Smart Query Analysis - Determine retrieval strategy
        if not skip_retrieval:
            query_complexity = analyze_query_complexity(effective_query)
        else:
            query_complexity = {'type': 'simple', 'confidence': 1.0}
        
        # 1b. CHAINED CONTEXT for Kira (Gemini Live style) was replaced by kira_processor logic above
        
        print(f"Query complexity: {query_complexity['type']} (confidence: {query_complexity['confidence']:.2f})")
        
        target_results = []
        if not skip_retrieval:
             # Override n_results for non-Kira to ensure broad search for reranking
             if persona != 'kira':
                 n_results = 50

             print(f"Retrieving {n_results} chunks for optimal context")
             print(f"Output language mode: {language}")

             # 2. Check Cache (using English query)
             # Note: For now, we skip cache for non-English to ensure proper language generation
             # In production, you might want to cache per language
             cache_entry = None
             if language == 'en':
                 cache_entry = core.get_cache_entry(effective_query)
             
             if cache_entry:
                 send_status("⚡ Finding answer from cache...")
                 print("Serving from cache...")
                 cached_answer, cached_sources = cache_entry
                 return iter([cached_answer]), cached_sources

             # 3. Retrieve Context (THE CORE LOGIC EXTRACTED)
             top_results = retrieve_context(
                 query_text=effective_query,
                 n_results=n_results,
                 language=language,
                 status_callback=send_status,
                 persona=persona,
                 query_complexity=query_complexity
             )
        else:
             top_results = [] # Chit chat = no context
             print("Skipping retrieval for Chit-Chat/Conversational turn.")

        
        if not top_results and not skip_retrieval:
            msg = "I couldn't find any relevant information in the uploaded documents."
            if language == 'hi':
                msg = "मुझे अपलोड किए गए दस्तावेज़ों में कोई प्रासंगिक जानकारी नहीं मिली।"
            return iter([msg]), []
            
        context_texts = [doc.page_content for doc, _ in top_results]
        source_filenames = {doc.metadata['filename'] for doc, _ in top_results if 'filename' in doc.metadata}
        context = "\n\n---\n\n".join(context_texts)
        
        # ChatML Prompt Construction for Qwen/Llama-Chat
        send_status("✍️ Generating final response...")
        if persona == 'kira':
             system_instruction = """You are Kira, a senior legal consultant on a live phone call. 
Your goal is to guide the user through their legal issue conversationally.

CRITICAL VOICE CONSTRAINTS:
1. NO MARKDOWN: Do not use **, ##, -, or list formats.
2. SHORT SENTENCES: Keep sentences under 15 words where possible. Long sentences confuse TTS.
3. CONVERSATIONAL FILLERS: Use phrases like "Let's see," "That's a good point," or "Bear with me."
4. ASK ONE THING: Never ask two questions in a row.
5. NO legal jargon without immediate explanation.

STRICT BEHAVIOR:
- If the retrieved text is insufficient, say: "I'm checking the files, but I don't see that specific detail here. Could you clarify...?"
- Do not cite Section numbers like a robot. Instead of "According to Section 103...", say "Under Section 103, the law states..."

CONVERSATIONAL APPROACH (INTERACTIVE MODE):
- This is a DIALOGUE, not a Q&A session. Engage naturally like a real legal consultation
- After providing information, ASK if they want more details, clarification, or related topics
- If the question is vague or broad, ask clarifying questions: "Are you asking about criminal liability or civil liability?" or "Could you tell me more about the specific situation?"
- Offer relevant follow-ups: "Would you like me to explain the procedure as well?" or "Should I also cover the exceptions to this rule?"
- Cross-question when needed: "Before I advise further, are you the plaintiff or defendant in this matter?"

CONSULTATION STYLE:
- Speak naturally as if you're sitting across from the client
- Think out loud: "Let me check the relevant provisions here... Okay, so based on what I'm seeing..."
- Reference documents conversationally: "The IT Act has specific guidelines on this..." or "I found a relevant case precedent..."
- Be warm yet professional, like a trusted advisor

RESPONSE STRUCTURE:
1. Address their immediate question briefly
2. Then ASK: clarifying questions OR offer to explore related aspects
3. Keep responses conversational and invite continued dialogue
3. Keep responses conversational and invite continued dialogue
"""
             prompt = f"<|im_start|>system\n{system_instruction}\nContext:\n{context}<|im_end|>\n"
        else:
            # STRICT ANTI-HALLUCINATION SYSTEM INSTRUCTION from File
            try:
                prompt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'STRICT_GROUNDING_PROMPT.txt')
                if os.path.exists(prompt_path):
                    with open(prompt_path, 'r', encoding='utf-8') as f:
                        template = f.read()
                    
                    # Fill the template
                    # Note: We include the query in the system prompt as per the rigid template structure
                    # This tells the model exactly what to answer based on the provided context.
                    filled_system_prompt = template.replace("{formatted_chunks}", context).replace("{query}", effective_query)
                    
                    # RESTORE LANGUAGE & CATEGORY INSTRUCTIONS
                    if category_tag and category_tag in tag_mapping:
                        category_name = tag_mapping[category_tag]
                        filled_system_prompt += f"\nIMPORTANT: Focus specifically on information related to {category_name}.\n"
                        
                    if language == 'hi':
                        filled_system_prompt += """
OUTPUT LANGUAGE REQUIREMENT:
- You MUST respond in Hindi using Devanagari script (हिंदी में उत्तर दें).
- Keep sentences short and clear.
"""
                    elif language == 'hi-romanized':
                        filled_system_prompt += """
OUTPUT LANGUAGE REQUIREMENT:
- You MUST respond in "Romanized Hindi" (Hinglish).
- Do not use Devanagari script.
- Example: "IPC Section 302 ke tehat punishment..."
"""
                    
                    prompt = f"<|im_start|>system\n{filled_system_prompt}<|im_end|>\n"
                    
                else:
                    # Fallback if file missing
                    raise FileNotFoundError("Prompt file not found")
            
            except Exception as e:
                print(f"Using fallback prompt: {e}")
                system_instruction = """You are a precise legal assistant.
Answer based ONLY on the provided context.
If the answer is not in the context, say "I don't have sufficient information".
Do not hallucinate citations.
"""
                prompt = f"<|im_start|>system\n{system_instruction}\nContext:\n{context}<|im_end|>\n<|im_start|>user\n{effective_query}<|im_end|>\n"
        
        if chat_history:
            # For Kira's interactive mode, use more history for better conversational context
            history_count = 10 if persona == 'kira' else 6
            for msg in chat_history[-history_count:]:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                # Note: History might be in Hindi if displayed in Hindi. 
                # Ideally we translate it, but for speed we omit history translation for now 
                # or rely on model to handle mixed context.
                if role == 'user':
                    prompt += f"<|im_start|>user\n{content}<|im_end|>\n"
                else:
                    prompt += f"<|im_start|>assistant\n{content}<|im_end|>\n"
        
        # Current turn (English) with SAFETY REMINDER
        safety_reminder = "\n\n🚨 REMINDER: Check every legal citation against the context above. If a Section/Article is not listed verbatim in the context, DO NOT cite it."
        final_query = effective_query + safety_reminder
        
        prompt += f"<|im_start|>user\n{final_query}<|im_end|>\n<|im_start|>assistant\n"

        print("Generating answer stream with ChatML...")
        stream = core.safe_llm_stream(prompt, stop=["<|im_end|>"])
        
        # Wrapper to handle caching
        def response_wrapper():
            full_answer_chunks = []
            
            # Stream the response directly (Qwen generates in the requested language)
            for chunk in stream:
                full_answer_chunks.append(chunk)
                yield chunk
            
            # Full answer text (in whatever language Qwen generated)
            full_text = "".join(full_answer_chunks)
            
            # 🚨 VERIFY LEGAL CITATIONS - Check for hallucinations
            verification = verify_legal_citations(full_text, context)
            
            if not verification['valid']:
                print(f"⚠️  CITATION VERIFICATION FAILED:")
                for violation in verification['violations']:
                    print(f"   {violation}")
                print(f"   📊 Stats: {verification['stats']}")
            else:
                stats = verification['stats']
                if stats['articles_cited'] > 0 or stats['sections_cited'] > 0:
                    print(f"✅ Citation verification passed: {stats['articles_cited']} articles, {stats['sections_cited']} sections verified")
            
            # Update Cache (only for English to keep cache simple)
            if language == 'en':
                core.update_cache(effective_query, full_text, list(source_filenames))
            
        return response_wrapper(), list(source_filenames)
        
    except Exception as e:
        print(f"Error during query: {e}")
        return iter(["An error occurred."]), []
