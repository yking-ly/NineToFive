"""
Quick test script to verify PDF parsing works correctly.
"""
import sys
from pathlib import Path

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.retrieval_engine.src.ingestion.pdf_parser import PDFParser

def main():
    # Path to test PDF
    pdf_path = project_root / "data" / "IPC_English.pdf"
    
    if not pdf_path.exists():
        print(f"[ERROR] PDF not found: {pdf_path}")
        return
    
    print(f"[PDF] Testing: {pdf_path.name}")
    print("=" * 60)
    
    # Initialize parser
    parser = PDFParser()
    
    # IPC_English.pdf structure:
    # Pages 1-13: Table of Contents (skip)
    # Pages 14-119: Actual sections (parse these)
    START_PAGE = 14
    END_PAGE = 119
    
    print(f"\n[Config] Parsing pages {START_PAGE} to {END_PAGE} (skipping TOC)")
    
    # Step 1: Extract raw text from content pages only
    print("\n[Step 1] Raw Text Extraction (pages 14-119)")
    print("-" * 40)
    text = parser.extract_text_from_pdf(pdf_path, start_page=START_PAGE, end_page=END_PAGE)
    print(f"Total characters extracted: {len(text)}")
    print(f"\nFirst 1000 characters:\n")
    print(text[:1000])
    print("\n... (truncated)")
    
    # Step 2: Parse sections from content pages
    print("\n\n[Step 2] Section Extraction")
    print("-" * 40)
    
    sections = list(parser.parse_ipc_bns_pdf(pdf_path, start_page=START_PAGE, end_page=END_PAGE))
    print(f"Total sections found: {len(sections)}")
    
    if sections:
        print("\nFirst 5 sections:")
        for i, section in enumerate(sections[:5]):
            print(f"\n  [{i+1}] Section {section.section_number}: {section.title[:50]}...")
            print(f"      Language: {section.language}")
            print(f"      Page: {section.page_number}")
            content_preview = section.content[:150] if section.content else "(empty)"
            print(f"      Content: {content_preview}...")
        
        print("\n\nLast 3 sections:")
        for i, section in enumerate(sections[-3:]):
            print(f"\n  Section {section.section_number}: {section.title[:50]}...")
            print(f"      Page: {section.page_number}")
    else:
        print("\n[WARNING] No sections extracted.")
    
    # Step 3: Show section distribution
    if sections:
        print("\n\n[Step 3] Section Statistics")
        print("-" * 40)
        
        # Content length stats
        lengths = [len(s.content) for s in sections]
        print(f"Shortest section: {min(lengths)} chars")
        print(f"Longest section: {max(lengths)} chars")
        print(f"Average section: {sum(lengths) // len(lengths)} chars")
        
        # Section number range
        section_nums = [s.section_number for s in sections]
        print(f"\nSection numbers: {section_nums[:5]} ... {section_nums[-5:]}")


if __name__ == "__main__":
    main()
