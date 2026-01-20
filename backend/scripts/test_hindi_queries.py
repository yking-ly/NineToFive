"""
Test bilingual retrieval - Query in Hindi, get results in both languages
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.retrieval_engine.src.config import settings
from services.retrieval_engine.src.vector_store.chroma_client import ChromaDBClient


def main():
    print("=" * 70)
    print("BILINGUAL RETRIEVAL TEST")
    print("Query in Hindi -> Get English + Hindi results")
    print("=" * 70)
    
    chroma = ChromaDBClient()
    
    # Hindi test queries
    hindi_queries = [
        "हत्या की सजा क्या है?",           # What is punishment for murder?
        "चोरी और डकैती",                    # Theft and robbery
        "धोखाधड़ी की परिभाषा",              # Definition of cheating
        "बलात्कार",                          # Rape
        "जालसाजी क्या है?",                 # What is forgery?
    ]
    
    for query in hindi_queries:
        print(f"\n{'─' * 70}")
        print(f"[QUERY] {query}")
        print("─" * 70)
        
        results = chroma.query(settings.IPC_COLLECTION, query, n_results=3)
        
        if results["documents"]:
            for i, (doc, meta, dist) in enumerate(zip(
                results["documents"], 
                results["metadatas"], 
                results["distances"]
            )):
                lang = meta.get('language', '??')
                lang_flag = "🇮🇳 HI" if lang == "hi" else "🇬🇧 EN"
                
                print(f"\n  [{i+1}] {lang_flag} | Section {meta.get('section_number')} | Distance: {dist:.4f}")
                print(f"      Title: {meta.get('section_title', '')[:50]}...")
                print(f"      Content: {doc[:120]}...")
        else:
            print("  No results found")
    
    # Also test English query for comparison
    print(f"\n\n{'=' * 70}")
    print("ENGLISH QUERY FOR COMPARISON")
    print("=" * 70)
    
    english_query = "What is the punishment for murder?"
    print(f"\n[QUERY] {english_query}")
    print("─" * 70)
    
    results = chroma.query(settings.IPC_COLLECTION, english_query, n_results=3)
    
    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"], 
        results["metadatas"], 
        results["distances"]
    )):
        lang = meta.get('language', '??')
        lang_flag = "HI" if lang == "hi" else "EN"
        
        print(f"\n  [{i+1}] {lang_flag} | Section {meta.get('section_number')} | Distance: {dist:.4f}")
        print(f"      Title: {meta.get('section_title', '')[:50]}...")


if __name__ == "__main__":
    main()
