import re

def clean_for_tts(text):
    """
    Post-processing to ensure clean audio output.
    1. Removes any residual markdown.
    2. Expands abbreviations that TTS might mispronounce (e.g., 'Sec.' -> 'Section').
    3. Adds pauses/breath markers if needed (heuristically).
    """
    # Remove markdown bold/italic/code identifiers
    text = re.sub(r"[\*\#\_`]", "", text)
    
    # Remove citations brackets like [1], [doc1.pdf] which break flow
    text = re.sub(r"\[.*?\]", "", text)
    
    # Expand common legal abbreviations for natural reading
    replacements = {
        "Sec.": "Section",
        "Art.": "Article",
        "v.": "versus",
        "Hon'ble": "Honorable",
        "SC": "Supreme Court",
        "HC": "High Court",
        "IPC": "I-P-C", 
        "CrPC": "Cr-P-C",
        "BNS": "B-N-S",
        "BNSS": "B-N-S-S",
        "FIR": "F-I-R",
        "vs": "versus"
    }
    
    for abbr, full in replacements.items():
        # Use word boundaries to avoid replacing substrings incorrectly
        text = re.sub(r'\b' + re.escape(abbr) + r'\b', full, text)
        
    # Ensure "Section" is fully written out if "Sec" appears without dot
    text = re.sub(r'\bSec\s+(\d+)', r'Section \1', text)

    return text.strip()

def detect_intent(query):
    """
    Simple heuristic intent detection.
    Returns: 'chit_chat', 'clarification', 'new_query'
    """
    q_lower = query.lower().strip()
    
    # Chit-Chat / Drivers
    greetings = ['hello', 'hi', 'hey', 'good morning', 'good evening', 'thanks', 'thank you', 'okay', 'ok', 'bye']
    if q_lower in greetings or len(q_lower.split()) < 2:
        return 'chit_chat'
        
    # Clarification (Dependent on previous context)
    clarifiers = ['what about', 'and if', 'is it', 'does it', 'why', 'how long', 'what if']
    if any(q_lower.startswith(c) for c in clarifiers):
        return 'clarification'
        
    return 'new_query'

def build_kira_context(history, query):
    """
    The 'Rewrite' Logic.
    Uses the last few turns to generate a standalone search query.
    If the user asks a clarification question, we attach the previous topic.
    """
    if not history:
        return query
        
    intent = detect_intent(query)
    
    # If it's chit-chat, we might not even need to rewrite, but let's pass it through
    if intent == 'chit_chat':
        return query
        
    # If clarification, try to find the last legal topic
    if intent == 'clarification' or len(query.split()) < 5:
        # Look back in history for the last user query or system response
        # This is a naive implementation; a real one would extract entities.
        # For now, we append the previous User Query which presumably had the context.
        
        # history[-1] is User (since we append current query to history only AFTER processing typically, 
        # BUT in app.py, history passed to retrieval usually excludes the CURRENT message being processed? 
        # Actually usually history is [User, AI, User, AI].
        # The 'query' arg is the CURRENT message.
        # So history[-1] is the LAST AI response. history[-2] is LAST USER message.
        
        if len(history) >= 2:
            last_user_msg = history[-2].get('content', '') if history[-2].get('role') == 'user' else ''
            # We assume the last user message had the core topic
            if last_user_msg:
                 return f"{query} (Context: {last_user_msg})"
                 
    return query

def generate_opener(query, intent=None):
    """
    Generates a fast, empathetic acknowledgment based on the query.
    This runs in parallel with the vector search.
    """
    import core
    
    if not intent:
        intent = detect_intent(query)
        
    if intent == 'chit_chat':
        # Don't need an elaborate opener for chit chat, just let the main model answer
        # Or return a quick "Hi there."
        return None
        
    prompt = f"""You are Kira, a helpful legal consultant.
User said: "{query}"
Task: Give a very short, natural, 1-sentence conversational acknowledgment to show you are listening and about to check the files.
Examples: 
- "That sounds like a serious situation, let me double check the specific section."
- "Okay, I see what you're asking, let me look that up."
- "Right, regarding bail, let me confirm the latest provisions."

Output ONLY the sentence. No quotes.
"""
    try:
        # Use a small token limit for speed
        # We assume core has a synchronous call or we consume the stream
        stream = core.safe_llm_stream(prompt, max_tokens=30)
        opener = "".join([chunk for chunk in stream])
        return opener.strip()
    except Exception as e:
        print(f"Opener generation failed: {e}")
        return "Let me check the files for you..."
