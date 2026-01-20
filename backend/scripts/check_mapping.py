"""
Check the ingested IPC-BNS Mappings
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.retrieval_engine.src.vector_store.chroma_client import ChromaDBClient

def main():
    print("=" * 60)
    print("INSPECTING MAPPING COLLECTION")
    print("=" * 60)
    
    chroma = ChromaDBClient()
    
    # 1. Check Count
    try:
        stats = chroma.get_collection_stats("mapping")
        print(f"\n[Status] Collection 'mapping' contains {stats['count']} entries.")
    except Exception as e:
        print(f"[Error] Could not access collection: {e}")
        return

    # 2. Run Sample Queries
    samples = [
        "Murder",             # Should find BNS 103 <-> IPC 302
        "Cheating",           # Should find BNS 318 <-> IPC 420
        "Unlawful Assembly",  # Should find BNS 189 <-> IPC 141
        "Section 302"         # Direct IPC lookup
    ]
    
    for q in samples:
        print(f"\n{'-'*60}")
        print(f"SEARCHING FOR: '{q}'")
        print(f"{'-'*60}")
        
        results = chroma.query("mapping", q, n_results=1)
        
        if results["ids"][0]:
            meta = results["metadatas"][0][0]
            doc = results["documents"][0][0]
            
            print(f"MATCH: BNS {meta.get('bns_section')} ↔ IPC {meta.get('ipc_section')}")
            print(f"Subject: {meta.get('subject')}")
            print(f"\nDocument Text:\n{doc}")
        else:
            print("No match found.")

if __name__ == "__main__":
    main()
