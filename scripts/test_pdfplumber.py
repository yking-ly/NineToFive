"""
Test BNS Hindi extraction with pdfplumber
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pdfplumber

def main():
    pdf_path = project_root / "data" / "BNS_Hindi.pdf"
    
    print(f"[PDF] Testing with pdfplumber: {pdf_path.name}")
    print("=" * 60)
    
    with pdfplumber.open(pdf_path) as pdf:
        # Check first few pages
        for i in range(min(4, len(pdf.pages))):
            page = pdf.pages[i]
            text = page.extract_text()
            print(f"\n[PAGE {i+1}] (first 500 chars):")
            if text:
                print(text[:500])
            else:
                print("(No text extracted)")
            print("-" * 40)

if __name__ == "__main__":
    main()
