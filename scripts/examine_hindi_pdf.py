"""
Examine Hindi PDF structure to understand format.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import fitz  # PyMuPDF

def main():
    pdf_path = project_root / "data" / "IPC_Hindi.pdf"
    
    if not pdf_path.exists():
        print(f"[ERROR] PDF not found: {pdf_path}")
        return
    
    print(f"[PDF] Examining: {pdf_path.name}")
    print("=" * 60)
    
    doc = fitz.open(pdf_path)
    print(f"Total pages: {len(doc)}")
    
    # Check first few pages to see TOC structure
    print("\n" + "-" * 40)
    print("PAGES 1-3 (Table of Contents?)")
    print("-" * 40)
    for i in range(min(3, len(doc))):
        text = doc[i].get_text()
        print(f"\n[PAGE {i+1}] (first 500 chars):")
        print(text[:500])
        print("...")
    
    # Check where content starts
    print("\n\n" + "-" * 40)
    print("LOOKING FOR CONTENT START...")
    print("-" * 40)
    
    for i in range(min(20, len(doc))):
        text = doc[i].get_text()
        # Look for "धारा 1" (Section 1) pattern
        if "धारा" in text and ("1." in text or "१." in text):
            print(f"\n[PAGE {i+1}] Found धारा (section) reference:")
            print(text[:800])
            break
    
    # Show a sample content page
    print("\n\n" + "-" * 40)
    print("SAMPLE CONTENT PAGE")
    print("-" * 40)
    
    # Try page 15-20 (likely content)
    for i in range(14, min(20, len(doc))):
        text = doc[i].get_text()
        if len(text) > 200:
            print(f"\n[PAGE {i+1}]:")
            print(text[:1500])
            break
    
    doc.close()


if __name__ == "__main__":
    main()
