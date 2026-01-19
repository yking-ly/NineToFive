"""
Examine BNS Hindi PDF structure
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import fitz  # PyMuPDF

def main():
    pdf_path = project_root / "data" / "BNS_Hindi.pdf"
    
    if not pdf_path.exists():
        print(f"[ERROR] PDF not found: {pdf_path}")
        return
    
    print(f"[PDF] Examining: {pdf_path.name}")
    print("=" * 60)
    
    doc = fitz.open(pdf_path)
    print(f"Total pages: {len(doc)}")
    
    # Check first few pages
    print("\n" + "-" * 40)
    print("PAGES 1-5")
    print("-" * 40)
    for i in range(min(5, len(doc))):
        text = doc[i].get_text()
        print(f"\n[PAGE {i+1}] (first 600 chars):")
        print(text[:600])
        print("...")
    
    # Check for Section 2 (definitions usually) or Section 103 (Murder)
    print("\n\n" + "-" * 40)
    print("SEARCHING FOR SECTIONS...")
    print("-" * 40)
    
    # Scan a few pages to see patterns
    for i in range(min(20, len(doc))):
        text = doc[i].get_text()
        # Look for patterns like "103." or "२."
        if "2." in text or "२." in text or "103." in text:
            print(f"\n[PAGE {i+1}] Content Sample:")
            print(text[:1000])
            break
            
    doc.close()

if __name__ == "__main__":
    main()
