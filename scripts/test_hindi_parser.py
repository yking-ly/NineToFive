"""
Test Hindi PDF parsing
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.retrieval_engine.src.ingestion.pdf_parser import PDFParser

def main():
    pdf_path = project_root / "data" / "IPC_Hindi.pdf"
    parser = PDFParser()
    
    print(f"[PDF] Testing: {pdf_path.name}")
    print("=" * 60)
    
    # Hindi PDF - content starts from page 1
    START_PAGE = 1
    END_PAGE = None  # All pages
    
    print(f"[Config] Parsing all pages (no TOC skip needed)")
    
    # Parse sections
    sections = list(parser.parse_ipc_bns_pdf(pdf_path, START_PAGE, END_PAGE))
    print(f"\nTotal sections found: {len(sections)}")
    
    if sections:
        print("\nFirst 5 sections:")
        for i, section in enumerate(sections[:5]):
            print(f"\n  [{i+1}] Section {section.section_number}")
            print(f"      Title: {section.title[:60]}...")
            print(f"      Language: {section.language}")
            content_preview = section.content[:100] if section.content else "(empty)"
            print(f"      Content: {content_preview}...")
        
        print("\n\nLast 3 sections:")
        for section in sections[-3:]:
            print(f"\n  Section {section.section_number}: {section.title[:40]}...")
        
        # Stats
        lengths = [len(s.content) for s in sections]
        print(f"\n\nStats:")
        print(f"  Shortest: {min(lengths)} chars")
        print(f"  Longest: {max(lengths)} chars")
        print(f"  Average: {sum(lengths) // len(lengths)} chars")
    else:
        print("\n[WARNING] No sections found!")


if __name__ == "__main__":
    main()
