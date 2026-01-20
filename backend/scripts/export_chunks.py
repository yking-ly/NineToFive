"""
View all chunks in ChromaDB collections.
Exports to JSON for easy inspection.
"""
import sys
import json
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))

from retrieval_engine.vector_store.chroma_client import ChromaDBClient

def export_collection(chroma, collection_name, output_file):
    """Export collection to JSON."""
    try:
        collection = chroma.get_or_create_collection(collection_name)
        results = collection.get(include=["documents", "metadatas"])
        
        data = []
        for i, doc_id in enumerate(results["ids"]):
            data.append({
                "id": doc_id,
                "document": results["documents"][i],  # Full text, no truncation
                "metadata": results["metadatas"][i]
            })
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Exported {len(data)} chunks from '{collection_name}' to {output_file}")
        return len(data)
    except Exception as e:
        print(f"✗ Failed to export '{collection_name}': {e}")
        return 0

def main():
    print("="*60)
    print("CHROMADB DATA EXPORT")
    print("="*60)
    
    chroma = ChromaDBClient()
    
    collections = ["ipc", "bns", "mapping", "case_law"]
    
    for col in collections:
        output_file = project_root / f"data/export_{col}.json"
        output_file.parent.mkdir(exist_ok=True)
        export_collection(chroma, col, output_file)
    
    print("\n✅ Done! Check the data/ folder for JSON files.")
    print("   Open them in VS Code or any JSON viewer.")

if __name__ == "__main__":
    main()
