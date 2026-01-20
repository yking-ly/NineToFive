"""
Debug script to examine PDF structure more closely.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.retrieval_engine.src.ingestion.pdf_parser import PDFParser

def main():
    pdf_path = project_root / "data" / "IPC_English.pdf"
    parser = PDFParser()
    
    # Extract text from a specific page to see the format
    text = parser.extract_text_from_pdf(pdf_path, start_page=14, end_page=16)
    
    print("=" * 60)
    print("RAW TEXT FROM PAGES 14-16")
    print("=" * 60)
    print(text[:4000])
    print("\n\n... continues ...")

if __name__ == "__main__":
    main()
