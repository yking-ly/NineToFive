"""
Test extracting mapping table using pdfplumber
"""
import sys
from pathlib import Path
import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    pdf_path = project_root / "data" / "IPC_BNS_Mapping_English.pdf"
    
    print(f"[PDF] Converting table: {pdf_path.name}")
    
    with pdfplumber.open(pdf_path) as pdf:
        # Check extraction on page 2 (index 1) which likely has different structure
        page = pdf.pages[1]
        
        print("\n--- extracting_tables() approach (PAGE 2) ---")
        tables = page.extract_tables()
        
        for i, table in enumerate(tables):
            print(f"\nTable {i+1}:")
            for row in table[:5]: # First 5 rows
                # Filter None values and clean newlines
                cleaned = [str(cell).replace('\n', ' ') if cell else '' for cell in row]
                print(cleaned)

if __name__ == "__main__":
    main()
