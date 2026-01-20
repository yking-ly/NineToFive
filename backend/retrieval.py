import core
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from deep_translator import GoogleTranslator
import re

# ============================================================================
# SMART RETRIEVAL HELPER FUNCTIONS
# ============================================================================

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

def generate_query_expansions(query: str, query_complexity: dict) -> List[str]:
    """
    Generates expanded queries for better retrieval coverage.
    """
    expansions = []
    query_lower = query.lower()
    
    # For comparative queries, split into component parts
    if query_complexity['type'] == 'comparative':
        if ' and ' in query_lower:
            parts = query_lower.split(' and ')
            expansions.extend(parts[:2])  # Take first two parts
        elif ' vs ' in query_lower or ' versus ' in query_lower:
            parts = re.split(r'\s+(?:vs|versus)\s+', query_lower)
            expansions.extend(parts[:2])
    
    # For complex queries, extract key concepts
    if query_complexity['type'] == 'complex':
        # Extract noun phrases (simplified)
        words = query.split()
        if len(words) > 5:
            # Take first half and second half as separate queries
            mid = len(words) // 2
            expansions.append(' '.join(words[:mid]))
            expansions.append(' '.join(words[mid:]))
    
    # Add legal term specific queries
    if query_complexity['keywords']:
        for term in query_complexity['keywords'][:2]:  # Limit to 2 terms
            expansions.append(term)
    
    # Limit total expansions
    return expansions[:3]

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
        # Create a simple hash of the content (first 200 chars)
        content_hash = hash(doc.page_content[:200])
        
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

def query_docs(query_text: str, chat_history: List[dict] = [], n_results: int = 3, language: str = 'en', category_tag: str = None, persona: str = 'default'):
    """
    Queries valid vector DBs (Persistent) + Answer Caching.
    Handles Translation for input (HI -> EN for retrieval).
    Supports three output modes: English, Hindi (Devanagari), Hindi (Romanized).
    Supports category filtering via tags (IPC, BNS, etc.)
    Supports 'persona' customization (e.g., 'kira').
    """
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
        
        # Adjust n_results for Kira (Knowledge at tip of tongue = more context)
        if persona == 'kira':
            n_results = max(n_results, 6)

        
        # 0. Handle Query Translation (Auto -> EN for retrieval)
        # We always process internally in English to use the English-optimized LLM and DB.
        effective_query = query_text
        needs_input_translation = False
        
        # If a category tag is selected, prepend it to help focus the search
        if category_tag and category_tag in tag_mapping:
            category_name = tag_mapping[category_tag]
            effective_query = f"{category_name}: {query_text}"
            print(f"Query refined with tag '{category_tag}': {effective_query}")
        
        # Translate input to English if it's in Hindi (both 'hi' and 'hi-romanized' might have Hindi input)
        if language in ['hi', 'hi-romanized']:
            try:
                # Translating query to English for retrieval
                translator = GoogleTranslator(source='auto', target='en')
                translated_query = translator.translate(effective_query)
                print(f"Translated input query: '{query_text}' -> '{translated_query}'")
                effective_query = translated_query
                needs_input_translation = True
            except Exception as e:
                print(f"Query translation failed: {e}")
                # Fallback to original, effectively treated as English
                effective_query = query_text if not category_tag else f"{tag_mapping.get(category_tag, '')}: {query_text}"

        # 1. Smart Query Analysis - Determine retrieval strategy
        query_complexity = analyze_query_complexity(effective_query)
        n_results = determine_chunk_count(query_complexity, category_tag)
        
        print(f"Query complexity: {query_complexity['type']} (confidence: {query_complexity['confidence']:.2f})")
        print(f"Retrieving {n_results} chunks for optimal context")
        print(f"Output language mode: {language}")

        # 2. Check Cache (using English query)
        # Note: For now, we skip cache for non-English to ensure proper language generation
        # In production, you might want to cache per language
        cache_entry = None
        if language == 'en':
            cache_entry = core.get_cache_entry(effective_query)
        
        if cache_entry:
            print("Serving from cache...")
            cached_answer, cached_sources = cache_entry
            return iter([cached_answer]), cached_sources

        # 3. Smart Multi-Strategy Search
        dbs = core.get_dbs()
        all_results = []
        
        # Strategy 1: Direct similarity search
        def search_shard(db):
            return db.similarity_search_with_score(effective_query, k=n_results)
        
        with ThreadPoolExecutor(max_workers=core.NUM_SHARDS) as executor:
            futures = [executor.submit(search_shard, db) for db in dbs]
            for future in as_completed(futures):
                try:
                    all_results.extend(future.result())
                except Exception as e:
                    print(f"Error querying shard: {e}")
        
        # Strategy 2: If query is complex, also search with expanded keywords
        if query_complexity['type'] in ['complex', 'comparative']:
            expanded_queries = generate_query_expansions(effective_query, query_complexity)
            print(f"Expanding search with {len(expanded_queries)} additional queries...")
            
            for exp_query in expanded_queries:
                with ThreadPoolExecutor(max_workers=core.NUM_SHARDS) as executor:
                    futures = [executor.submit(lambda db: db.similarity_search_with_score(exp_query, k=2), db) for db in dbs]
                    for future in as_completed(futures):
                        try:
                            all_results.extend(future.result())
                        except Exception as e:
                            print(f"Error in expanded query: {e}")
        
        # Remove duplicates based on content similarity
        all_results = deduplicate_results(all_results)
        
        # Sort by score (lower is better for L2)
        all_results.sort(key=lambda x: x[1])
        
        # Smart filtering: Apply relevance threshold
        relevance_threshold = get_relevance_threshold(query_complexity)
        filtered_results = [r for r in all_results if r[1] <= relevance_threshold]
        
        if not filtered_results:
            print(f"No results below threshold {relevance_threshold}, using top results anyway")
            filtered_results = all_results
        
        # Take top K from filtered results
        top_results = filtered_results[:n_results]
        
        print(f"Selected {len(top_results)} chunks from {len(all_results)} total results")
        
        if not top_results:
            msg = "I couldn't find any relevant information in the uploaded documents."
            if language == 'hi':
                msg = "मुझे अपलोड किए गए दस्तावेज़ों में कोई प्रासंगिक जानकारी नहीं मिली।"
            elif language == 'hi-romanized':
                msg = "Mujhe upload kiye gaye dastavez mein koi prasangik jaankari nahi mili."
            return iter([msg]), []
            
        context_texts = []
        source_filenames = set()
        
        for doc, score in top_results:
            context_texts.append(doc.page_content)
            if 'filename' in doc.metadata:
                source_filenames.add(doc.metadata['filename'])
                
        context = "\n\n---\n\n".join(context_texts)
        
        # ChatML Prompt Construction for Qwen/Llama-Chat
        if persona == 'kira':
             system_instruction = """You are Kira, a Legal Advisor having a live, interactive voice consultation with a client.

CRITICAL OUTPUT RULE: You MUST respond in PURE PLAINTEXT ONLY. Absolutely NO formatting characters.

FORBIDDEN FORMATTING (NEVER USE):
- NO asterisks, underscores, hashtags, backticks, dashes for formatting
- NO bold, italic, headers, code blocks, or lists with special characters
- Output pure spoken language only

CONVERSATIONAL APPROACH (INTERACTIVE MODE):
- This is a DIALOGUE, not a Q&A session. Engage naturally like a real legal consultation
- After providing information, ASK if they want more details, clarification, or related topics
- If the question is vague or broad, ask clarifying questions: "Are you asking about criminal liability or civil liability?" or "Could you tell me more about the specific situation?"
- Offer relevant follow-ups: "Would you like me to explain the procedure as well?" or "Should I also cover the exceptions to this rule?"
- Cross-question when needed: "Before I advise further, are you the plaintiff or defendant in this matter?"
- Remember the conversation context and build on previous exchanges

CONSULTATION STYLE:
- Speak naturally as if you're sitting across from the client
- Think out loud: "Let me check the relevant provisions here... Okay, so based on what I'm seeing..."
- Reference documents conversationally: "The IT Act has specific guidelines on this..." or "I found a relevant case precedent..."
- Be warm yet professional, like a trusted advisor
- Don't just dump information - guide the conversation based on their needs

RESPONSE STRUCTURE:
1. Address their immediate question briefly
2. Then ASK: clarifying questions OR offer to explore related aspects
3. Keep responses conversational and invite continued dialogue

EXAMPLES OF INTERACTIVE RESPONSES:
- "Section 302 deals with murder and prescribes either death or life imprisonment. Now, is this for a case you're researching, or do you need to understand the defenses available? I can explain either."
- "The IT Act covers that under Section 66. Before I dive deeper, are you concerned about data breach penalties or the compliance requirements? Both are important but quite different."
- "I see provisions on this in both the IPC and BNS. The punishment varies. Would you like me to compare them, or focus on the current applicable law?"

Your goal: Create a flowing, two-way conversation where the client feels heard, can ask follow-ups naturally, and receives guidance tailored to their actual needs.
"""
        else:
            # Base system instruction
            system_instruction = """You are a precise legal assistant.
Task: Answer the user's question using ONLY the provided context. If the answer is not in the context, say so.
"""
        
        # Add category-specific instruction if tag is provided
        if category_tag and category_tag in tag_mapping:
            category_name = tag_mapping[category_tag]
            system_instruction += f"\nIMPORTANT: Focus specifically on information related to {category_name}. Prioritize content from this legal domain.\n"
        
        # Add language-specific output instructions
        if language == 'hi':
            system_instruction += """
OUTPUT LANGUAGE REQUIREMENT:
- You MUST respond in Hindi using Devanagari script (हिंदी में उत्तर दें)
- Write your entire response in proper Hindi
- Use appropriate Hindi legal terminology
- Maintain professional Hindi language throughout
"""
        elif language == 'hi-romanized':
            system_instruction += """
OUTPUT LANGUAGE REQUIREMENT:
- You MUST respond in Hindi but written in Roman script (Latin alphabet)
- Example: "Dhara 302 ke antargat..." instead of "धारा 302 के अंतर्गत..."
- Use Romanized Hindi (Hinglish) throughout your response
- Transliterate Hindi words to Roman script
- This is also known as "Roman Hindi" or "Hinglish"
"""
        
        # Only add markdown formatting constraints for non-Kira personas
        if persona != 'kira':
            system_instruction += """
STRICT CONSTRAINTS:
1.  **Format**: Use Markdown (bolding, lists, code blocks).
2.  **Length**: Concise but complete.
3.  **Completeness**: Finish sentences.
4.  **Citations**: Cite sources if available.
"""

        prompt = f"<|im_start|>system\n{system_instruction}\nContext:\n{context}<|im_end|>\n"
        
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
        
        # Current turn (English)
        prompt += f"<|im_start|>user\n{effective_query}<|im_end|>\n<|im_start|>assistant\n"

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
            
            # Update Cache (only for English to keep cache simple)
            if language == 'en':
                core.update_cache(effective_query, full_text, list(source_filenames))
            
        return response_wrapper(), list(source_filenames)
        
    except Exception as e:
        print(f"Error during query: {e}")
        return iter(["An error occurred."]), []
