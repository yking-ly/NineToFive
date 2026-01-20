"""
Test BNS PDF parsing
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.retrieval_engine.src.ingestion.pdf_parser import PDFParser

def main():
    pdf_path = project_root / "data" / "BNS_English.pdf"
    parser = PDFParser()
    
    print(f"[PDF] Testing: {pdf_path.name}")
    print("=" * 60)
    
    # BNS English - content starts from page 16
    START_PAGE = 16
    END_PAGE = None 
    
    print(f"[Config] Parsing from page {START_PAGE}")
    
    # Parse sections
    sections = list(parser.parse_ipc_bns_pdf(pdf_path, START_PAGE, END_PAGE))
    print(f"\nTotal sections found: {len(sections)}")
    
    if sections:
        print("\nFirst 5 sections:")
        for i, section in enumerate(sections[:5]):
            print(f"\n  [{i+1}] Section {section.section_number}")
            print(f"      Title: {section.title[:60]}...")
            content_preview = section.content[:100] if section.content else "(empty)"
            print(f"      Content: {content_preview}...")
        
        print("\n\nLast 3 sections:")
        for section in sections[-3:]:
             print(f"\n  Section {section.section_number}: {section.title[:50]}...")

    else:
        print("\n[WARNING] No sections found! Check regex/page range.")

if __name__ == "__main__":
    main()
