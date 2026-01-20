"""
Test retrieval explicitly from the BNS collection
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.retrieval_engine.src.config import settings
from services.retrieval_engine.src.vector_store.chroma_client import ChromaDBClient

def main():
    print("=" * 60)
    print("TESTING BNS COLLECTION RETRIEVAL")
    print("=" * 60)
    
    chroma = ChromaDBClient()
    
    # Verify count first
    try:
        stats = chroma.get_collection_stats("bns")
        print(f"\n[Status] BNS Collection has {stats['count']} documents")
    except Exception as e:
        print(f"\n[Error] Could not access BNS collection: {e}")
        return

    # BNS specific queries
    # Note: In BNS, Murder is Section 103 (was 302 in IPC)
    queries = [
        "What is the punishment for murder?",
        "Organized crime",   # New concept in BNS
        "Mob lynching",      # New concept in BNS
        "Definition of rape" # Section 63 in BNS (was 375 in IPC)
    ]
    
    for query in queries:
        print(f"\n{'─' * 60}")
        print(f"[Query] {query}")
        print("─" * 60)
        
        results = chroma.query("bns", query, n_results=2)
        
        if results["documents"]:
            for i, (doc, meta, dist) in enumerate(zip(
                results["documents"], 
                results["metadatas"], 
                results["distances"]
            )):
                print(f"\n  Result {i+1} (distance: {dist:.4f}):")
                print(f"    Section: {meta.get('section_number')}")
                print(f"    Title: {meta.get('section_title', '')[:60]}...")
                print(f"    Preview: {doc[:150]}...")
        else:
            print("  No results found")

if __name__ == "__main__":
    main()
