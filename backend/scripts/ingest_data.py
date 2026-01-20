"""
Data Ingestion Script - Loads PDFs into ChromaDB

Usage:
    uv run python backend/scripts/ingest_data.py --all
    uv run python backend/scripts/ingest_data.py --ipc
    uv run python backend/scripts/ingest_data.py --bns
"""
import sys
from pathlib import Path

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8')

# Add backend directory to path (scripts is now at backend/scripts/)
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import argparse
from retrieval_engine.config import settings
from retrieval_engine.ingestion.pdf_parser import PDFParser
from retrieval_engine.vector_store.chroma_client import ChromaDBClient


# PDF Page Configurations (skip TOC, parse content only)
PDF_CONFIG = {
    "IPC_English.pdf": {"start_page": 14, "end_page": 119},
    "IPC_Hindi.pdf": {"start_page": 1, "end_page": None},  # Hindi has no TOC
    "BNS_English.pdf": {"start_page": 16, "end_page": None},
    "BNS_Hindi.pdf": {"start_page": 2, "end_page": None}, # Text starts on page 2 in simple OCR
}


def ingest_ipc(parser: PDFParser, chroma: ChromaDBClient):
    """Ingest IPC documents into ChromaDB."""
    print("\n" + "=" * 60)
    print("INGESTING IPC DOCUMENTS")
    print("=" * 60)
    
    ipc_files = [
        settings.DATA_DIR / "IPC_English.pdf",
        settings.DATA_DIR / "IPC_Hindi.pdf",  # Hindi enabled
    ]
    
    all_chunks = []
    
    for pdf_path in ipc_files:
        if not pdf_path.exists():
            print(f"[SKIP] {pdf_path.name} not found")
            continue
        
        config = PDF_CONFIG.get(pdf_path.name, {})
        start_page = config.get("start_page")
        end_page = config.get("end_page")
        
        print(f"\n[PDF] Processing: {pdf_path.name}")
        print(f"      Pages: {start_page} to {end_page or 'end'}")
        
        section_count = 0
        for section in parser.parse_ipc_bns_pdf(pdf_path, start_page, end_page):
            # Create chunk (one section = one chunk)
            for chunk in parser.chunk_section(section):
                all_chunks.append(chunk)
            section_count += 1
        
        print(f"      Sections extracted: {section_count}")
    
    # Deduplicate chunks by ID (keep first occurrence only)
    seen_ids = set()
    unique_chunks = []
    for chunk in all_chunks:
        if chunk["id"] not in seen_ids:
            seen_ids.add(chunk["id"])
            unique_chunks.append(chunk)
    
    if len(unique_chunks) < len(all_chunks):
        print(f"      [Dedupe] Removed {len(all_chunks) - len(unique_chunks)} duplicates")
    
    # Add to ChromaDB
    if unique_chunks:
        print(f"\n[ChromaDB] Adding {len(unique_chunks)} chunks to '{settings.IPC_COLLECTION}'...")
        added = chroma.add_documents(settings.IPC_COLLECTION, unique_chunks)
        print(f"[OK] Added {added} documents to ChromaDB")
    else:
        print("\n[WARNING] No chunks to add")
    
    return len(all_chunks)


def ingest_bns(parser: PDFParser, chroma: ChromaDBClient):
    """Ingest BNS documents into ChromaDB."""
    print("\n" + "=" * 60)
    print("INGESTING BNS DOCUMENTS")
    print("=" * 60)
    
    bns_files = [
        settings.DATA_DIR / "BNS_English.pdf",
        settings.DATA_DIR / "BNS_Hindi.pdf",
    ]
    
    all_chunks = []
    
    for pdf_path in bns_files:
        if not pdf_path.exists():
            print(f"[SKIP] {pdf_path.name} not found")
            continue
        
        config = PDF_CONFIG.get(pdf_path.name, {})
        start_page = config.get("start_page")
        end_page = config.get("end_page")
        
        print(f"\n[PDF] Processing: {pdf_path.name}")
        print(f"      Pages: {start_page or 1} to {end_page or 'end'}")
        
        # Use OCR for BNS Hindi
        use_ocr = "BNS_Hindi.pdf" in pdf_path.name
        if use_ocr:
             print("      [Mode] Using OCR extraction (this will be slow...)")

        section_count = 0
        for section in parser.parse_ipc_bns_pdf(pdf_path, start_page, end_page, use_ocr=use_ocr):
            for chunk in parser.chunk_section(section):
                all_chunks.append(chunk)
            section_count += 1
        
        print(f"      Sections extracted: {section_count}")
    
    # Add to ChromaDB
    if all_chunks:
        print(f"\n[ChromaDB] Adding {len(all_chunks)} chunks to '{settings.BNS_COLLECTION}'...")
        added = chroma.add_documents(settings.BNS_COLLECTION, all_chunks)
        print(f"[OK] Added {added} documents to ChromaDB")
    else:
        print("\n[WARNING] No chunks to add")
    
    return len(all_chunks)


def test_retrieval(chroma: ChromaDBClient):
    """Test retrieval from ChromaDB."""
    print("\n" + "=" * 60)
    print("TESTING RETRIEVAL")
    print("=" * 60)
    
    test_queries = [
        "What is the punishment for murder?",
        "theft and robbery",
        "definition of cheating",
    ]
    
    for query in test_queries:
        print(f"\n[Query] {query}")
        results = chroma.query(settings.IPC_COLLECTION, query, n_results=2)
        
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


def main():
    parser = argparse.ArgumentParser(description="Ingest legal documents into ChromaDB")
    parser.add_argument("--all", action="store_true", help="Ingest all documents")
    parser.add_argument("--ipc", action="store_true", help="Ingest IPC documents")
    parser.add_argument("--bns", action="store_true", help="Ingest BNS documents")
    parser.add_argument("--test", action="store_true", help="Test retrieval after ingestion")
    parser.add_argument("--clear", action="store_true", help="Clear collections before ingestion")
    
    args = parser.parse_args()
    
    # Default to --all if no specific option
    if not (args.ipc or args.bns):
        args.all = True
    
    # Initialize
    print("[Init] Initializing PDF Parser...")
    pdf_parser = PDFParser()
    
    print("[Init] Initializing ChromaDB Client...")
    print(f"       Persist directory: {settings.CHROMA_PERSIST_DIR}")
    chroma = ChromaDBClient()
    
    # Clear if requested
    if args.clear:
        print("\n[Clear] Deleting existing collections...")
        if args.all or args.ipc:
            chroma.delete_collection(settings.IPC_COLLECTION)
            print(f"        Deleted: {settings.IPC_COLLECTION}")
        if args.all or args.bns:
            chroma.delete_collection(settings.BNS_COLLECTION)
            print(f"        Deleted: {settings.BNS_COLLECTION}")
    
    # Ingest
    total_chunks = 0
    
    if args.all or args.ipc:
        total_chunks += ingest_ipc(pdf_parser, chroma)
    
    if args.all or args.bns:
        total_chunks += ingest_bns(pdf_parser, chroma)
    
    # Summary
    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"Total chunks added: {total_chunks}")
    
    # Collection stats
    print("\nCollection Statistics:")
    for collection in [settings.IPC_COLLECTION, settings.BNS_COLLECTION]:
        try:
            stats = chroma.get_collection_stats(collection)
            print(f"  {stats['name']}: {stats['count']} documents")
        except Exception:
            print(f"  {collection}: (not created)")
    
    # Test retrieval
    if args.test or True:  # Always test
        test_retrieval(chroma)


if __name__ == "__main__":
    main()
