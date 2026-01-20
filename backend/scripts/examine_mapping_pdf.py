"""
Examine IPC-BNS Mapping PDF
"""
import sys
from pathlib import Path
import fitz  # PyMuPDF

sys.stdout.reconfigure(encoding='utf-8')
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    pdf_path = project_root / "data" / "IPC_BNS_Mapping_English.pdf"
    
    if not pdf_path.exists():
        print(f"[ERROR] PDF not found: {pdf_path}")
        return
    
    print(f"[PDF] Examining: {pdf_path.name}")
    doc = fitz.open(pdf_path)
    
    # Check first few pages
    for i in range(min(5, len(doc))):
        text = doc[i].get_text()
        print(f"\n[PAGE {i+1}]")
        print(text[:800])
        print("...")

if __name__ == "__main__":
    main()
