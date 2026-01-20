"""
Ingest IPC-BNS Mapping into ChromaDB
"""
import sys
from pathlib import Path
import pdfplumber
import re

sys.stdout.reconfigure(encoding='utf-8')

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from retrieval_engine.vector_store.chroma_client import ChromaDBClient
from retrieval_engine.config import settings

def clean_text(text):
    if not text:
        return ""
    return str(text).replace('\n', ' ').strip()

def parse_mapping_pdf(pdf_path):
    print(f"[Parser] Reading {pdf_path.name}...")
    mappings = []
    
    unique_counter = 0

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            
            for table in tables:
                for row in table:
                    # Safe index access
                    def get_col(idx):
                        if idx < len(row):
                            return clean_text(row[idx])
                        return ""
                    
                    if not row:
                         continue
                         
                    # Dynamic Column Parsing
                    # Page 1 has 6 cols (indices 0,3,4,5 relevant)
                    # Page 2+ has 4 cols (indices 0,1,2,3 relevant)
                    
                    bns_sec = ""
                    subject = ""
                    ipc_sec = ""
                    summary = ""
                    
                    # Remove empty strings from row to see actual data structure
                    data_cols = [c for c in row if c and str(c).strip()]
                    
                    if len(row) >= 6:
                        # Page 1 Format
                        bns_sec = get_col(0)
                        subject = get_col(3)
                        ipc_sec = get_col(4)
                        summary = get_col(5)
                    elif len(row) == 4:
                        # Standard Format (Page 2+)
                        bns_sec = get_col(0)
                        subject = get_col(1)
                        ipc_sec = get_col(2)
                        summary = get_col(3)
                    elif len(data_cols) == 4:
                         # Fallback: if there are exactly 4 data columns, assume they are BNS, Subject, IPC, Summary
                         bns_sec = clean_text(data_cols[0])
                         subject = clean_text(data_cols[1])
                         ipc_sec = clean_text(data_cols[2])
                         summary = clean_text(data_cols[3])
                    else:
                        # Fallback for complex merged rows or headers
                        # Try to use Index 0 as BNS
                        bns_sec = get_col(0)
                        if not bns_sec: continue
                        # Try to find IPC (usually short, digits or 'New')
                        # This is risky, so we skip if we can't determine strict format
                        pass

                    # Skip header rows
                    if "BNS" in bns_sec or "Summary" in summary or "Subject" in subject:
                        continue
                    if not bns_sec and not subject and not ipc_sec: continue
                        
                    clean_ipc = ipc_sec
                    if not clean_ipc or clean_ipc == "-" or "New" in clean_ipc:
                        is_new = True 
                        mapped_ipc = "None (New in BNS)" if "New" in clean_ipc else "None"
                    else:
                        is_new = False
                        mapped_ipc = clean_ipc
                    
                    if bns_sec:
                        unique_counter += 1
                        # Totally safe ID: "map_INDEX_bns_X_ipc_Y"
                        entry_id = f"map_{unique_counter}_bns_{bns_sec}_ipc_{mapped_ipc}".replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_").replace("-", "").replace(".", "")[:63] # Limit length
                        
                        entry = {
                            "bns_section": bns_sec,
                            "ipc_section": clean_ipc if clean_ipc else "-",
                            "subject": subject,
                            "summary": summary,
                            "is_new": is_new,
                            "id": entry_id
                        }
                        
                        # Create semantic document for RAG
                        doc_text = (
                            f"BNS to IPC Mapping:\n"
                            f"BNS Section: {bns_sec}\n"
                            f"IPC Section: {mapped_ipc}\n"
                            f"Subject: {subject}\n"
                            f"Comparison: {summary}"
                        )
                        
                        mappings.append({
                            "id": entry["id"],
                            "document": doc_text,
                            "metadata": entry
                        })
    
    return mappings

def main():
    pdf_path = settings.DATA_DIR / "IPC_BNS_Mapping_English.pdf"
    
    if not pdf_path.exists():
        print("Mapping PDF not found!")
        return
        
    # Parse
    mappings = parse_mapping_pdf(pdf_path)
    print(f"\n[Parser] Found {len(mappings)} mappings.")
    
    if not mappings:
        print("[Error] No mappings extracted. Check parser logic.")
        return
        
    # Preview
    print("\nFirst 3 mappings:")
    for m in mappings[:3]:
        print(f"  {m['metadata']['bns_section']} <-> {m['metadata']['ipc_section']}")
        print(f"  {m['document'][:100]}...")
        print()
        
    # Ingest
    chroma = ChromaDBClient()
    collection_name = "mapping"
    
    print(f"\n[Chroma] Ingesting into '{collection_name}'...")
    chroma.delete_collection(collection_name) # Reset
    chroma.add_documents(collection_name, mappings)
    print("[Success] Mapping ingestion complete.")

if __name__ == "__main__":
    main()
