"""
Document Processor with Smart Text Extraction
Implements: Text Extraction → OCR Fallback → LLM Summary → Vector DB Ingestion
"""

import os
import io
import sys
import platform
from typing import Tuple, Optional
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import docx
from langchain_community.document_loaders import PyPDFLoader, TextLoader

try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.docstore.document import Document

import core

# Configure Tesseract path for Windows
if platform.system() == 'Windows':
    tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    else:
        print("⚠️  Warning: Tesseract not found at default Windows path.")
        print("   Install from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("   Or set custom path: pytesseract.pytesseract.tesseract_cmd = 'your_path'")



def extract_text_from_pdf(file_path: str) -> Tuple[str, str]:
    """
    Primary method: Extract text programmatically from PDF
    
    Returns:
        Tuple[str, str]: (extracted_text, method_used)
    """
    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        text = "\n".join([d.page_content for d in docs])
        
        # Check if extraction was successful (non-empty and meaningful)
        if text.strip() and len(text.strip()) > 50:
            return text, "standard_extraction"
        else:
            return "", "empty_extraction"
    except Exception as e:
        print(f"Standard PDF extraction failed: {e}")
        return "", "extraction_failed"


def extract_text_with_ocr(file_path: str) -> Tuple[str, str]:
    """
    Fallback method: Use OCR for scanned PDFs or image-based documents
    
    Returns:
        Tuple[str, str]: (extracted_text, method_used)
    """
    try:
        print("  → Falling back to OCR extraction...")
        
        # Convert PDF pages to images
        images = convert_from_path(file_path, dpi=300)  # High DPI for better OCR
        
        all_text = []
        for i, image in enumerate(images):
            print(f"    → OCR processing page {i + 1}/{len(images)}...")
            
            # Perform OCR on each page
            text = pytesseract.image_to_string(image, lang='eng+hin')  # English + Hindi support
            all_text.append(text)
        
        combined_text = "\n\n".join(all_text)
        
        if combined_text.strip():
            return combined_text, "ocr_extraction"
        else:
            return "", "ocr_failed"
            
    except Exception as e:
        print(f"OCR extraction failed: {e}")
        return "", "ocr_error"


def extract_text_from_docx(file_path: str) -> Tuple[str, str]:
    """
    Extract text from DOCX files
    
    Returns:
        Tuple[str, str]: (extracted_text, method_used)
    """
    try:
        doc = docx.Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs]
        text = "\n".join(paragraphs)
        
        if text.strip():
            return text, "docx_extraction"
        else:
            return "", "docx_empty"
    except Exception as e:
        print(f"DOCX extraction failed: {e}")
        return "", "docx_error"


def extract_text_from_txt(file_path: str) -> Tuple[str, str]:
    """
    Extract text from TXT files
    
    Returns:
        Tuple[str, str]: (extracted_text, method_used)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if text.strip():
            return text, "txt_extraction"
        else:
            return "", "txt_empty"
    except Exception as e:
        print(f"TXT extraction failed: {e}")
        return "", "txt_error"


def extract_text_smart(file_path: str) -> Tuple[str, str]:
    """
    Smart text extraction with automatic fallback mechanism
    
    Strategy:
    1. Try standard programmatic extraction first
    2. If that fails, fallback to OCR
    3. Return both text and the method used
    
    Returns:
        Tuple[str, str]: (extracted_text, method_used)
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        # Try standard extraction first
        text, method = extract_text_from_pdf(file_path)
        
        # If standard extraction failed, try OCR
        if not text or method in ["empty_extraction", "extraction_failed"]:
            print(f"  ⚠️  Standard extraction {method}, trying OCR...")
            text, method = extract_text_with_ocr(file_path)
        
        return text, method
    
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    
    elif ext == '.txt':
        return extract_text_from_txt(file_path)
    
    else:
        return "", "unsupported_format"


def generate_summary_with_qwen(text: str, max_context: int = 4000) -> str:
    """
    Generate document summary using local Qwen LLM
    
    Args:
        text: Full document text
        max_context: Maximum characters to send to LLM
    
    Returns:
        str: Generated summary
    """
    try:
        # Truncate text to fit context window
        context = text[:max_context] if len(text) > max_context else text
        
        # ChatML format for Qwen
        prompt = f"""<|im_start|>system
You are a legal document analysis assistant. Provide clear, structured summaries of legal documents.
Focus on key points, definitions, scope, and important provisions.<|im_end|>
<|im_start|>user
Analyze and summarize the following document in a clear, professional manner:

{context}

Provide a comprehensive summary that:
1. States the document type and purpose
2. Lists key provisions and definitions
3. Highlights important clauses or sections
4. Mentions the scope and applicability<|im_end|>
<|im_start|>assistant
"""
        
        summary = core.safe_llm_invoke(prompt, stop=["<|im_end|>"])
        
        # Clean up summary
        summary = summary.strip()
        
        return summary if summary else "Summary generation completed, but no content was produced."
    
    except Exception as e:
        print(f"Error generating summary: {e}")
        return f"Summary generation failed: {str(e)}"


def process_document_complete(file_path: str, filename: str) -> dict:
    """
    Complete document processing pipeline as per flowchart:
    1. Text Extraction (with OCR fallback)
    2. Summary Generation using Local Qwen
    3. Return processing results
    
    Note: Ingestion to Vector DB is handled separately to maintain separation of concerns
    
    Returns:
        dict: Processing results including text, summary, and metadata
    """
    print(f"\n{'='*60}")
    print(f"Processing Document: {filename}")
    print(f"{'='*60}")
    
    # Step 1: Smart Text Extraction (with OCR fallback)
    print("\n[Step 1/2] Extracting text...")
    extracted_text, extraction_method = extract_text_smart(file_path)
    
    if not extracted_text:
        return {
            "success": False,
            "error": f"Failed to extract text. Method: {extraction_method}",
            "extraction_method": extraction_method
        }
    
    print(f"  ✅ Text extracted successfully using: {extraction_method}")
    print(f"  📊 Extracted {len(extracted_text)} characters")
    
    # Step 2: Generate Summary using Local Qwen
    print("\n[Step 2/2] Generating AI summary with local Qwen...")
    summary = generate_summary_with_qwen(extracted_text)
    
    print(f"  ✅ Summary generated successfully")
    print(f"  📝 Summary length: {len(summary)} characters")
    
    print(f"\n{'='*60}")
    print("✅ Document processing complete!")
    print(f"{'='*60}\n")
    
    return {
        "success": True,
        "text": extracted_text,
        "summary": summary,
        "extraction_method": extraction_method,
        "text_length": len(extracted_text),
        "summary_length": len(summary),
        "filename": filename
    }


def generate_contextual_insights(file_text: str, vector_db_context: str, filename: str) -> str:
    """
    Generate insights by comparing document content with existing knowledge base
    This implements the "explain in 5 simple points using vector db but ignore current file" requirement
    
    Args:
        file_text: Text from the current uploaded document
        vector_db_context: Retrieved context from vector database (excluding current file)
        filename: Name of the current file (for filtering)
    
    Returns:
        str: 5-point explanation based on existing knowledge
    """
    try:
        prompt = f"""<|im_start|>system
You are analyzing a legal document database. You have access to existing documents and knowledge.
Your task is to explain key concepts related to the uploaded document using ONLY your existing knowledge,
NOT the content of the newly uploaded document itself.<|im_end|>
<|im_start|>user
A new document "{filename}" has been uploaded. Based on your existing knowledge base (shown below),
explain in 5 simple, clear points what the legal concepts, principles, or frameworks are that relate
to this type of document.

EXISTING KNOWLEDGE BASE:
{vector_db_context}

Provide exactly 5 clear points that explain the legal framework or context related to this document type.
Do NOT directly cite or reference the newly uploaded document - only use your existing knowledge.<|im_end|>
<|im_start|>assistant
Based on the existing legal knowledge base, here are 5 key points:

"""
        
        insights = core.safe_llm_invoke(prompt, stop=["<|im_end|>"], max_tokens=500)
        
        return insights.strip()
    
    except Exception as e:
        print(f"Error generating contextual insights: {e}")
        return "Could not generate contextual insights at this time."
