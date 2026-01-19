"""
Examine BNS English PDF structure
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import fitz  # PyMuPDF

def main():
    pdf_path = project_root / "data" / "BNS_English.pdf"
    
    if not pdf_path.exists():
        print(f"[ERROR] PDF not found: {pdf_path}")
        return
    
    print(f"[PDF] Examining: {pdf_path.name}")
    print("=" * 60)
    
    doc = fitz.open(pdf_path)
    print(f"Total pages: {len(doc)}")
    
    # Check pages 1-5 (likely TOC intro)
    print("\n" + "-" * 40)
    print("PAGES 1-5 (Introduction/TOC)")
    print("-" * 40)
    for i in range(min(5, len(doc))):
        text = doc[i].get_text()
        print(f"\n[PAGE {i+1}] ({len(text)} chars):")
        print(text[:400] if text.strip() else "(empty or image)")
        print("...")
    
    # Check page 14-16 (transition from TOC to content)
    print("\n\n" + "-" * 40)
    print("PAGES 14-17 (TOC → Content transition)")
    print("-" * 40)
    for i in range(13, min(17, len(doc))):
        text = doc[i].get_text()
        print(f"\n[PAGE {i+1}] ({len(text)} chars):")
        print(text[:600])
        print("...")
    
    # Find where actual content starts
    print("\n\n" + "-" * 40)
    print("CONTENT SAMPLE (Page 16-18)")
    print("-" * 40)
    for i in range(15, min(18, len(doc))):
        text = doc[i].get_text()
        print(f"\n[PAGE {i+1}]:")
        print(text[:1200])
        print("...")
    
    doc.close()


if __name__ == "__main__":
    main()
