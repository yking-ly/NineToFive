"""
Inspect all collections in ChromaDB
"""
import sys
from pathlib import Path
import random

sys.stdout.reconfigure(encoding='utf-8')
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.retrieval_engine.src.vector_store.chroma_client import ChromaDBClient

def main():
    chroma = ChromaDBClient()
    
    print("=" * 80)
    print("CHROMADB INSPECTOR")
    print("=" * 80)
    
    # 1. List Collections (Hardcoded based on our knowledge, or query if API supported)
    # Chroma client wrapper usually needs specific collection names
    collections = ["ipc", "bns", "mapping"]
    
    for name in collections:
        print(f"\n[{name.upper()} COLLECTION]")
        print("-" * 80)
        
        try:
            coll = chroma.client.get_collection(name)
            count = coll.count()
            print(f"Total Documents: {count}")
            
            if count > 0:
                # Get a slightly larger batch to pick random samples from
                # Chroma doesn't support "random" natively well without fetching IDs first
                # We'll just fetch the first 10 and pick from there, or a slice
                
                # Fetching first 5 just to show structure
                data = coll.get(limit=5)
                
                ids = data['ids']
                metadatas = data['metadatas']
                documents = data['documents']
                
                print("\nSample Entries:")
                for i in range(min(3, len(ids))):
                    print(f"\n  Document ID: {ids[i]}")
                    print(f"  Metadata:    {metadatas[i]}")
                    # Truncate document text for display
                    doc_preview = documents[i].replace('\n', ' ')[:100] + "..."
                    print(f"  Content:     {doc_preview}")
            else:
                print("  (Empty)")
                
        except Exception as e:
            print(f"  Error accessing collection: {e}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
