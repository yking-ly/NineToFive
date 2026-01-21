"""
Ollama LLM Service for local language model inference.

Connects to Ollama running on localhost:11434.
"""

import requests
import json
from typing import Optional


class OllamaService:
    """Service for interacting with local Ollama LLM."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "legal-llama"):
        """
        Initialize Ollama connection.
        
        Args:
            base_url: Ollama API URL (default localhost:11434)
            model: Model name to use (default qwen2.5:7b)
        """
        self.base_url = base_url
        self.model = model
        self.enabled = False
        
        # Test connection
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self.enabled = True
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                print(f"[Ollama] Connected. Available models: {model_names}")
                
                # Check if our model is available
                if not any(self.model in name for name in model_names):
                    print(f"[Ollama Warning] Model '{self.model}' not found. Available: {model_names}")
            else:
                print(f"[Ollama Warning] Connection failed: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("[Ollama Warning] Ollama not running. LLM features disabled.")
        except Exception as e:
            print(f"[Ollama Warning] Error: {e}")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                 temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            temperature: Creativity (0-1)
            max_tokens: Max response length
            
        Returns:
            Generated text response
        """
        if not self.enabled:
            return "[LLM Error] Ollama is not available."
        
        # Build the full prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                },
                timeout=180  # LLM can be slow, especially first load
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                return f"[LLM Error] Generation failed: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "[LLM Error] Request timed out. The model may be loading."
        except Exception as e:
            return f"[LLM Error] {str(e)}"
    
    def chat(self, messages: list, temperature: float = 0.7) -> str:
        """
        Chat-style interaction with the LLM.
        
        Args:
            messages: List of {"role": "user"|"assistant"|"system", "content": "..."}
            temperature: Creativity (0-1)
            
        Returns:
            Generated response
        """
        if not self.enabled:
            return "[LLM Error] Ollama is not available."
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "")
            else:
                return f"[LLM Error] Chat failed: {response.status_code}"
                
        except Exception as e:
            return f"[LLM Error] {str(e)}"
    
    def generate_legal_answer(self, query: str, context: dict, response_language: str = 'en') -> str:
        """
        Generate a legal answer using retrieved context.
        
        Args:
            query: The user's question
            context: Retrieved context from RAG
            response_language: 'en', 'hi', or 'hinglish'
        """
        # Build context string from retrieved results
        context_parts = []
        
        # Quick mapping (instant lookup) - prioritize this
        if context.get("quick_mapping"):
            for qm in context["quick_mapping"]:
                context_parts.append(
                    f"[EXACT MATCH] IPC Section {qm.get('ipc')} = BNS Section {qm.get('bns')} "
                    f"(Category: {qm.get('category', 'Unknown')})"
                )
        
        if context.get("mapping"):
            for item in context["mapping"][:2]:
                meta = item.get("metadata", {})
                context_parts.append(
                    f"[MAPPING] IPC {meta.get('ipc_section')} → BNS {meta.get('bns_section')}: "
                    f"{meta.get('subject')}. Changes: {meta.get('summary')}"
                )
        
        if context.get("ipc"):
            for item in context["ipc"][:2]:
                meta = item.get("metadata", {})
                context_parts.append(
                    f"[IPC Section {meta.get('section_number')}] {meta.get('section_title')}: "
                    f"{item.get('text', '')[:500]}"
                )
        
        if context.get("bns"):
            for item in context["bns"][:2]:
                meta = item.get("metadata", {})
                context_parts.append(
                    f"[BNS Section {meta.get('section_number')}] {meta.get('section_title')}: "
                    f"{item.get('text', '')[:500]}"
                )
        
        # Add Case Law context for precedents
        if context.get("case_law"):
            for item in context["case_law"][:2]:  # Top 2 cases by relevance
                meta = item.get("metadata", {})
                case_title = meta.get("case_title", "Unknown Case")
                case_date = meta.get("case_date", "")
                year = meta.get("year", "")
                sections = meta.get("sections_mentioned", "")
                
                # Check if landmark
                is_landmark = meta.get("is_landmark", False)
                if isinstance(is_landmark, str):
                    is_landmark = is_landmark.lower() in ['true', '1', 'yes']
                
                landmark_badge = "⭐ LANDMARK JUDGMENT" if is_landmark else "Case Law"
                relevance_score = item.get("relevance_score", 0)
                
                context_parts.append(
                    f"[{landmark_badge}] {case_title} ({case_date or year}) [Relevance: {relevance_score:.0f}/100]\n"
                    f"Sections referenced: {sections}\n"
                    f"Excerpt: {item.get('text', '')[:400]}"
                )
        
        # Add Constitution context
        if context.get("constitution"):
            for item in context["constitution"][:3]:  # Top 3 articles/sections
                meta = item.get("metadata", {})
                articles = meta.get("articles_mentioned", "")
                parts = meta.get("parts_mentioned", "")
                
                article_info = f"Articles: {articles}" if articles else ""
                part_info = f"Part: {parts}" if parts else ""
                location = " | ".join(filter(None, [article_info, part_info]))
                
                context_parts.append(
                    f"[CONSTITUTION OF INDIA] {location}\n"
                    f"Excerpt: {item.get('text', '')[:500]}"
                )
        
        context_str = "\n\n".join(context_parts)
        
        # System prompt for legal assistant - varies by response language
        base_system = """You are an expert Indian legal assistant. Your role is to:
1. Explain legal concepts clearly and accurately
2. Reference specific IPC/BNS sections when relevant
3. Highlight the transition from IPC to BNS (new criminal law)
4. Cite relevant case law precedents when available
5. Be helpful but remind users to consult a lawyer for serious matters

Use the provided context to answer. If case law is provided, reference it for precedents.
Format your answer with clear headings and bullet points where appropriate."""

        # Adjust system prompt based on response language
        if response_language == 'hinglish':
            system_prompt = base_system + """

IMPORTANT: Respond in HINGLISH (Hindi words written in English/Roman letters, NOT Devanagari script).
Example: "Murder ki saza maut ya umar kaid hai. IPC Section 302 ke tahat..."
Keep legal terms and section numbers in English. Use common Hindi words in Roman script."""
        else:
            system_prompt = base_system

        user_prompt = f"""Question: {query}

Relevant Legal Context:
{context_str}

Please provide a comprehensive answer based on the context above."""

        return self.generate(user_prompt, system_prompt=system_prompt, temperature=0.3)


# Test if run directly
if __name__ == "__main__":
    llm = OllamaService()
    
    if llm.enabled:
        print("\nTesting generation...")
        response = llm.generate("What is Section 302 of IPC?")
        print(f"Response: {response[:500]}...")
    else:
        print("Ollama not available. Start it with: ollama serve")
