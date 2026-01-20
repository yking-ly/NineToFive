"""
Case Law Ingestion Script
Ingests Supreme Court judgments into ChromaDB for RAG.

Usage:
    python backend/scripts/ingest_case_law.py --years 10    # Last 10 years
    python backend/scripts/ingest_case_law.py --all         # All years (slow!)
"""

import sys
import os
from pathlib import Path
import argparse
from datetime import datetime

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.resolve()
project_root = backend_dir.parent.resolve()
sys.path.insert(0, str(backend_dir))

from retrieval_engine.vector_store.chroma_client import ChromaDBClient
from retrieval_engine.ingestion.pdf_parser import PDFParser

# Configuration
CASE_LAW_DIR = project_root / "data" / "case_law" / "supreme_court_judgments"
COLLECTION_NAME = "case_law"
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200


def parse_case_filename(filename: str) -> dict:
    """
    Parse case metadata from filename.
    Example: 'Arvind_Kejriwal_vs_Directorate_Of_Enforcement_on_10_May_2024_1.PDF'
    """
    name = filename.replace(".PDF", "").replace(".pdf", "")
    parts = name.rsplit("_on_", 1)
    
    if len(parts) == 2:
        parties = parts[0].replace("_", " ")
        date_part = parts[1].rsplit("_", 1)[0]  # Remove trailing _1
        
        # Try to parse date
        try:
            # Format: "10_May_2024" -> "10 May 2024"
            date_str = date_part.replace("_", " ")
            case_date = datetime.strptime(date_str, "%d %B %Y").strftime("%Y-%m-%d")
        except:
            case_date = "Unknown"
        
        # Split parties
        if " vs " in parties.lower():
            petitioner, respondent = parties.lower().split(" vs ", 1)
            petitioner = petitioner.title()
            respondent = respondent.title()
        else:
            petitioner = parties
            respondent = "Unknown"
        
        return {
            "petitioner": petitioner,
            "respondent": respondent,
            "case_date": case_date,
            "case_title": parties
        }
    
    return {
        "petitioner": "Unknown",
        "respondent": "Unknown", 
        "case_date": "Unknown",
        "case_title": name.replace("_", " ")
    }


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind('. ')
            if last_period > chunk_size // 2:
                end = start + last_period + 1
                chunk = text[start:end]
        
        chunks.append(chunk.strip())
        start = end - overlap
    
    return chunks


import re

def extract_sections_from_text(text: str) -> dict:
    """
    Extract IPC/BNS section references from judgment text.
    
    Returns:
        dict with:
            - sections: list of section numbers (e.g., ["302", "120B", "420"])
            - acts: list of acts mentioned (e.g., ["IPC", "BNS", "PMLA"])
    """
    # Pattern for section numbers
    section_pattern = r'(?:Section|Sec\.?|धारा)\s*(\d+[A-Za-z]?(?:\s*\(\d+\))?)'
    sections = re.findall(section_pattern, text, re.IGNORECASE)
    
    # Clean up section numbers
    sections = [re.sub(r'\s+', '', s) for s in sections]  # Remove whitespace
    sections = list(set(sections))[:20]  # Unique, max 20
    
    # Pattern for acts
    acts_found = []
    if re.search(r'\bIPC\b|Indian Penal Code', text, re.IGNORECASE):
        acts_found.append("IPC")
    if re.search(r'\bBNS\b|Bharatiya Nyaya Sanhita', text, re.IGNORECASE):
        acts_found.append("BNS")
    if re.search(r'\bCrPC\b|Criminal Procedure', text, re.IGNORECASE):
        acts_found.append("CrPC")
    if re.search(r'\bPMLA\b|Prevention of Money Laundering', text, re.IGNORECASE):
        acts_found.append("PMLA")
    if re.search(r'\bNDPS\b|Narcotic Drugs', text, re.IGNORECASE):
        acts_found.append("NDPS")
    if re.search(r'\bPOCSO\b|Protection of Children', text, re.IGNORECASE):
        acts_found.append("POCSO")
    
    return {
        "sections": sections,
        "acts": acts_found
    }


def ingest_year(year_dir: Path, parser: PDFParser, chroma: ChromaDBClient, year: str, limit: int = None) -> int:
    """Ingest all PDFs from a year directory."""
    pdf_files = list(year_dir.glob("*.PDF")) + list(year_dir.glob("*.pdf"))
    
    # Apply limit if specified
    if limit and limit > 0:
        pdf_files = pdf_files[:limit]
        print(f"  [Limit] Processing only {limit} PDFs")
    
    if not pdf_files:
        print(f"  No PDFs found in {year}")
        return 0
    
    documents = []
    
    for pdf_path in pdf_files:
        try:
            # Extract text from PDF
            text_parts = []
            for page_num, text in parser.extract_text_from_pdf(str(pdf_path)):
                text_parts.append(text)
            
            full_text = "\n".join(text_parts)
            
            if len(full_text.strip()) < 100:
                continue  # Skip empty/corrupt PDFs
            
            # Parse metadata from filename
            metadata = parse_case_filename(pdf_path.name)
            metadata["year"] = year
            metadata["source"] = "Supreme Court of India"
            metadata["filename"] = pdf_path.name
            
            # Extract section references from the full text
            section_info = extract_sections_from_text(full_text)
            metadata["sections_mentioned"] = ",".join(section_info["sections"])  # Store as comma-separated
            metadata["acts_mentioned"] = ",".join(section_info["acts"])
            
            # Chunk the text
            chunks = chunk_text(full_text)
            
            for i, chunk in enumerate(chunks):
                doc_id = f"case_{year}_{pdf_path.stem}_{i}"
                documents.append({
                    "id": doc_id,
                    "document": chunk,
                    "metadata": {
                        **metadata,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                })
        
        except Exception as e:
            print(f"  [Error] Failed to process {pdf_path.name}: {e}")
            continue
    
    # Ingest to ChromaDB
    if documents:
        chroma.add_documents(COLLECTION_NAME, documents)
        print(f"  ✓ {year}: Ingested {len(documents)} chunks from {len(pdf_files)} PDFs")
    
    return len(documents)


def main():
    parser_args = argparse.ArgumentParser(description="Ingest Supreme Court case law")
    parser_args.add_argument("--years", type=int, default=10, help="Number of recent years to ingest")
    parser_args.add_argument("--year", type=str, help="Specific year to ingest (e.g., 2024)")
    parser_args.add_argument("--all", action="store_true", help="Ingest all years")
    parser_args.add_argument("--limit", type=int, default=None, help="Max PDFs per year (for testing)")
    args = parser_args.parse_args()
    
    if not CASE_LAW_DIR.exists():
        print(f"[Error] Case law directory not found: {CASE_LAW_DIR}")
        return
    
    # Get available years
    year_dirs = sorted([d for d in CASE_LAW_DIR.iterdir() if d.is_dir()], reverse=True)
    
    # Determine which years to process
    if args.year:
        # Specific year
        year_dir = CASE_LAW_DIR / args.year
        if year_dir.exists():
            years_to_process = [year_dir]
        else:
            print(f"[Error] Year {args.year} not found")
            return
    elif args.all:
        years_to_process = year_dirs
    else:
        years_to_process = year_dirs[:args.years]
    
    print(f"\n{'='*60}")
    print(f"CASE LAW INGESTION")
    print(f"{'='*60}")
    print(f"Source: {CASE_LAW_DIR}")
    print(f"Years to process: {len(years_to_process)}")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"{'='*60}\n")
    
    # Initialize
    pdf_parser = PDFParser()
    chroma = ChromaDBClient()
    
    total_chunks = 0
    
    for year_dir in years_to_process:
        year = year_dir.name
        chunks_added = ingest_year(year_dir, pdf_parser, chroma, year, limit=args.limit)
        total_chunks += chunks_added
    
    print(f"\n{'='*60}")
    print(f"INGESTION COMPLETE")
    print(f"Total chunks ingested: {total_chunks}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
