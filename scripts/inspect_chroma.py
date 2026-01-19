"""
Inspect ChromaDB collections and data.
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
    print("CHROMADB INSPECTOR")
    print("=" * 60)
    
    # Check if DB exists
    db_path = settings.CHROMA_PERSIST_DIR / "chroma.sqlite3"
    print(f"\nDatabase path: {db_path}")
    print(f"Database exists: {db_path.exists()}")
    
    if not db_path.exists():
        print("\n[INFO] No ChromaDB database found. Run ingestion first.")
        return
    
    # Connect to ChromaDB
    chroma = ChromaDBClient()
    
    # List all collections
    print("\n" + "-" * 40)
    print("COLLECTIONS")
    print("-" * 40)
    
    collections = chroma.client.list_collections()
    if not collections:
        print("No collections found.")
        return
    
    for col in collections:
        print(f"\n  Collection: {col.name}")
        print(f"  Count: {col.count()} documents")
    
    # Inspect each collection
    for col in collections:
        print("\n" + "-" * 40)
        print(f"COLLECTION: {col.name}")
        print("-" * 40)
        
        # Get sample documents
        count = col.count()
        if count == 0:
            print("  (empty)")
            continue
        
        # Get first 5 documents
        sample = col.get(
            limit=5,
            include=["documents", "metadatas"]
        )
        
        print(f"\nSample documents (showing {len(sample['ids'])} of {count}):\n")
        
        for i, (doc_id, doc, meta) in enumerate(zip(
            sample['ids'], 
            sample['documents'], 
            sample['metadatas']
        )):
            print(f"  [{i+1}] ID: {doc_id}")
            print(f"      Section: {meta.get('section_number', 'N/A')}")
            print(f"      Title: {meta.get('section_title', 'N/A')[:50]}...")
            print(f"      Language: {meta.get('language', 'N/A')}")
            print(f"      Content preview: {doc[:100]}...")
            print()


if __name__ == "__main__":
    main()
