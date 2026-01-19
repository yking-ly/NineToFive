"""
Dump the first few entries of the mapping collection to verify structure
"""
import sys
from pathlib import Path
import pandas as pd # Use pandas for nice table display

sys.stdout.reconfigure(encoding='utf-8')
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.retrieval_engine.src.vector_store.chroma_client import ChromaDBClient

def main():
    chroma = ChromaDBClient()
    
    print("=" * 100)
    print(f"{'BNS Section':<15} | {'IPC Section':<20} | {'Subject':<30} | {'Comparison Summary (Preview)'}")
    print("=" * 100)

    try:
        # Access the raw collection to get data without semantic search
        coll = chroma.client.get_collection("mapping")
        
        # Get ALL items
        data = coll.get(limit=2000)
        
        metadatas = data['metadatas']
        
        # Prepare list for DataFrame
        rows = []
        
        for meta in metadatas:
            bns = meta.get('bns_section', 'N/A')
            ipc = meta.get('ipc_section', 'N/A')
            subj = meta.get('subject', 'N/A')
            summ = meta.get('summary', 'N/A')
            
            rows.append({
                "BNS Section": bns,
                "IPC Section": ipc,
                "Subject": subj,
                "Comparison": summ
            })
            
            # Print simplified version to terminal
            subj_short = subj[:28] + ".." if len(subj) > 28 else subj
            summ_short = summ[:40] + "..." if len(summ) > 40 else summ
            print(f"{bns:<15} | {ipc:<20} | {subj_short:<30} | {summ_short}")

        # Save to CSV
        try:
            df = pd.DataFrame(rows)
            # Sort by BNS section (nicer view) - simple string sort
            df = df.sort_values(by="BNS Section") 
            output_file = project_root / "bns_ipc_mapping_full.csv"
            df.to_csv(output_file, index=False)
            print("=" * 100)
            print(f"[SUCCESS] All {len(rows)} mappings saved to: {output_file}")
            print(f"You can open this file in VS Code or Excel to filter/search.")
        except Exception as csv_err:
            print(f"[Warning] Could not save CSV: {csv_err}")

    except Exception as e:
        print(f"[Error] Failed to read collection: {e}")

if __name__ == "__main__":
    main()
