"""
Test OCR extraction for BNS Hindi using EasyOCR
"""
import sys
from pathlib import Path
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

sys.stdout.reconfigure(encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pypdfium2 as pdfium
import easyocr
import numpy as np

def main():
    pdf_path = project_root / "data" / "BNS_Hindi.pdf"
    
    print(f"[OCR] Testing EasyOCR on: {pdf_path.name}")
    print("=" * 60)
    print("Initializing Reader (this loads the model, might take a minute)...")
    
    reader = easyocr.Reader(['hi', 'en'], gpu=False, verbose=False)
    
    print("\nProcessing Page 2 (where text starts)...")
    
    try:
        pdf_doc = pdfium.PdfDocument(pdf_path)
        page = pdf_doc[1]  # 0-indexed, so 1 is page 2
        
        # Render page to PIL image
        bitmap = page.render(scale=2)  # scale=2 for better OCR quality
        img = bitmap.to_pil()
        # Convert to numpy for EasyOCR
        img_np = np.array(img)
        
    except Exception as e:
        print(f"\n[ERROR] Image extraction failed: {e}")
        return
    
    print("Extracting text...")
    result = reader.readtext(img_np, detail=0, paragraph=True)
    
    print("\n" + "-" * 40)
    print("EXTRACTED TEXT")
    print("-" * 40)
    
    full_text = "\n".join(result)
    print(full_text)
    print("-" * 40)

if __name__ == "__main__":
    main()
