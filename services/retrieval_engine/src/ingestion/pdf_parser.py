"""
PDF Parser for extracting text from legal documents.
Handles IPC, BNS, and Mapping PDFs.
"""
import fitz  # PyMuPDF
import re
from pathlib import Path
from typing import Generator
from dataclasses import dataclass


@dataclass
class Section:
    """Represents a legal section extracted from PDF."""
    section_number: str
    title: str
    content: str
    language: str  # 'en' or 'hi'
    page_number: int
    chapter: Optional[str] = None
    

@dataclass
class MappingEntry:
    """Represents an IPC to BNS mapping entry."""
    ipc_section: str
    bns_section: str
    ipc_title: str
    bns_title: str
    change_type: str  # 'renumbered', 'modified', 'new', 'repealed'
    language: str
    notes: str = ""


class PDFParser:
    """Parser for legal PDF documents."""
    
    # Regex patterns for section extraction
    # - Allow optional 1-2 digit footnote refs before section (e.g., "9[4." means section 4)
    # - Section number: 1-3 digits (1-999), optional letter suffix (A-Z)
    # - Title must contain em-dash (—) or double-dash (––) - IPC uses —, BNS uses ––
    # - This filters out footnotes which don't have dashes
    SECTION_PATTERN_EN = re.compile(
        r'(?:^|\n)(?:\d{1,2}\[)?(\d{1,3}[A-Z]?)\.\s+([^—–\n]+(?:—|––)[^\n]*)\n(.*?)(?=(?:^|\n)(?:\d{1,2}\[)?\d{1,3}[A-Z]?\.\s+[A-Z][^—–]*(?:—|––)|\Z)',
        re.DOTALL
    )
    # Hindi pattern - uses same structure but with Devanagari numerals support
    # Updated for BNS Hindi which often lacks titles/dashes (e.g. "1. (1)...")
    SECTION_PATTERN_HI = re.compile(
        r'(?:^|\n)(\d{1,3}[कखगघङ]?|[०-९]+)\.\s+(.*?)(?=(?:^|\n)(?:\d{1,3}[कखगघङ]?|[०-९]+)\.\s+|\Z)',
        re.DOTALL
    )
    
    def __init__(self):
        # Initialize reader lazily only if needed to save RAM
        self.ocr_reader = None

    def _get_ocr_reader(self):
        if self.ocr_reader is None:
            print("[OCR] Initializing EasyOCR model (this may take a moment)...")
            self.ocr_reader = easyocr.Reader(['hi', 'en'], gpu=False, verbose=False)
        return self.ocr_reader

    def extract_text_from_pdf_ocr(self, pdf_path: str, start_page: int = 1, end_page: Optional[int] = None) -> Generator[Tuple[int, str], None, None]:
        """
        Extract text from PDF using OCR (for image-based or garbled PDFs).
        Yields (page_number, text).
        """
        reader = self._get_ocr_reader()
        pdf_doc = pdfium.PdfDocument(pdf_path)
        total_pages = len(pdf_doc)
        
        start = max(0, start_page - 1)
        end = end_page if end_page else total_pages
        
        print(f"[OCR] Processing pages {start+1} to {end}...")
        
        for i in range(start, end):
            try:
                page = pdf_doc[i]
                # Render to image (scale=2 for better quality)
                bitmap = page.render(scale=2)
                img = bitmap.to_pil()
                img_np = np.array(img)
                
                # Extract text
                result = reader.readtext(img_np, detail=0, paragraph=True)
                text = "\n".join(result)
                
                yield (i + 1, text)
                
            except Exception as e:
                print(f"[Error] OCR failed on page {i+1}: {e}")
                yield (i + 1, "")

    def extract_text_from_pdf(self, pdf_path: str, start_page: int = 1, end_page: Optional[int] = None) -> Generator[Tuple[int, str], None, None]:
        """
        Extract text from PDF page by page using PyMuPDF (standard text extraction).
        Yields (page_number, text).
        """
        doc = fitz.open(pdf_path)
        
        # Adjust 1-based index to 0-based
        start_idx = max(0, start_page - 1)
        end_idx = min(end_page, len(doc)) if end_page else len(doc)
        
        for i in range(start_idx, end_idx):
            page = doc[i]
            text = page.get_text()
            yield (i + 1, text)
            
        doc.close()
    
    def detect_language(self, filename: str) -> str:
        """Detect language from filename."""
        if "_Hindi" in filename or "_hindi" in filename:
            return "hi"
        return "en"
    
    def detect_source(self, filename: str) -> str:
        """Detect document source from filename."""
        filename_lower = filename.lower()
        if "mapping" in filename_lower:
            return "mapping"
        elif "bns" in filename_lower:
            return "bns"
        elif "ipc" in filename_lower:
            return "ipc"
        return "unknown"
    
    def parse_ipc_bns_pdf(self, pdf_path: Any, start_page: int = 1, end_page: Optional[int] = None, use_ocr: bool = False) -> Generator[Section, None, None]:
        """
        Parse IPC/BNS PDF and yield Sections.
        
        Args:
            pdf_path: Path to PDF file
            start_page: Page to start parsing from (1-indexed)
            end_page: Page to stop parsing at (1-indexed)
            use_ocr: Whether to use OCR for text extraction
        """
        path_obj = str(pdf_path)
        filename = pdf_path.name if hasattr(pdf_path, 'name') else str(pdf_path)
        is_hindi = "Hindi" in filename
        section_pattern = self.SECTION_PATTERN_HI if is_hindi else self.SECTION_PATTERN_EN
        
        # Buffer to hold text across pages to handle sections spanning pages
        full_text_buffer = ""
        page_map = [] # Track which character index corresponds to which page (approx)
        
        current_char_count = 0
        
        # Choose extraction method
        extractor = self.extract_text_from_pdf_ocr if use_ocr else self.extract_text_from_pdf
        
        for page_num, text in extractor(path_obj, start_page, end_page):
            full_text_buffer += text + "\n"
            # Record that text up to this current length belongs to this page
            page_map.append((len(full_text_buffer), page_num))
            
            # Optimization: Process buffer periodically if it gets too large?
            # For legal docs, sections can be long, but usually keeping full text matches is safer 
            # for regex across boundaries.
        
        # Find all matches
        for match in section_pattern.finditer(full_text_buffer):
            sec_num = match.group(1)
            
            if is_hindi and use_ocr:
                # BNS Hindi (OCR) often lacks a clear title line, content starts immediately
                # Group 2 is "content" in our updated permissive regex
                title = "Section " + sec_num # Generic title as fallback
                content = match.group(2).strip()
                
                # Try to extract a real title if the first line looks like one
                first_line = content.split('\n')[0]
                if len(first_line) < 100:
                    title = first_line
            else:
                title = match.group(2).strip()
                content = match.group(3).strip()
            
            # Find page number based on match start position
            match_start = match.start()
            page_num = start_page # Default
            for length, p_num in page_map:
                if match_start < length:
                    page_num = p_num
                    break
            
            yield Section(
                source=filename,
                section_number=sec_num,
                title=title,
                content=content,
                language="hi" if is_hindi else "en",
                page_number=page_num,
                chapter=None # Chapter extraction needs more complex parsing
            )
    
    def parse_mapping_pdf(self, pdf_path: Path) -> Generator[MappingEntry, None, None]:
        """
        Parse IPC-BNS Mapping PDF and yield mapping entries.
        """
        text = self.extract_text_from_pdf(pdf_path)
        language = self.detect_language(pdf_path.name)
        
        # Pattern for mapping entries (adjust based on actual PDF structure)
        # Format: IPC Section | BNS Section | Status/Notes
        mapping_pattern = re.compile(
            r'(\d+[A-Z]?)\s*[|\-→]\s*(\d+[A-Z]?)\s*[|\-]?\s*([^\n]*)',
            re.IGNORECASE
        )
        
        for match in mapping_pattern.finditer(text):
            ipc_sec = match.group(1).strip()
            bns_sec = match.group(2).strip()
            notes = match.group(3).strip() if match.group(3) else ""
            
            # Determine change type based on notes
            change_type = "renumbered"
            notes_lower = notes.lower()
            if "modif" in notes_lower or "amend" in notes_lower:
                change_type = "modified"
            elif "new" in notes_lower or "added" in notes_lower:
                change_type = "new"
            elif "repeal" in notes_lower or "omit" in notes_lower:
                change_type = "repealed"
            
            yield MappingEntry(
                ipc_section=ipc_sec,
                bns_section=bns_sec,
                ipc_title="",  # To be enriched later
                bns_title="",  # To be enriched later
                change_type=change_type,
                language=language,
                notes=notes
            )
    
    def chunk_section(
        self, 
        section: Section, 
        split_large: bool = False,
        chunk_size: int = 1000, 
        overlap: int = 200
    ) -> Generator[dict, None, None]:
        """
        Chunk a section for embedding.
        
        For legal documents, sections are atomic semantic units.
        By default, we keep each section as ONE chunk (no splitting).
        
        Args:
            section: The section to chunk
            split_large: If True, split sections > chunk_size (not recommended for legal)
            chunk_size: Max size if splitting (default 1000)
            overlap: Overlap if splitting (default 200)
        """
        content = f"Section {section.section_number}: {section.title}\n\n{section.content}"
        
        # Default: One section = One chunk (recommended for legal docs)
        if not split_large or len(content) <= chunk_size:
            # Use hash of content to ensure uniqueness
            import hashlib
            content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
            yield {
                "id": f"{section.source}_sec_{section.section_number}_{section.language}_{content_hash}",
                "document": content,
                "metadata": {
                    "source": section.source,
                    "section_number": section.section_number,
                    "section_title": section.title,
                    "language": section.language,
                    "page_number": section.page_number,
                    "chapter": section.chapter,
                    "chunk_index": 0,
                    "total_chunks": 1,
                    "char_count": len(content)
                }
            }
        else:
            # Only split if explicitly requested (for very long sections)
            chunks = []
            start = 0
            chunk_idx = 0
            
            while start < len(content):
                end = start + chunk_size
                chunk = content[start:end]
                chunks.append((chunk_idx, chunk))
                start = end - overlap
                chunk_idx += 1
            
            for idx, chunk_text in chunks:
                yield {
                    "id": f"{section.source}_sec_{section.section_number}_{section.language}_chunk_{idx}",
                    "document": chunk_text,
                    "metadata": {
                        "source": section.source,
                        "section_number": section.section_number,
                        "section_title": section.title,
                        "language": section.language,
                        "page_number": section.page_number,
                        "chapter": section.chapter,
                        "chunk_index": idx,
                        "total_chunks": len(chunks),
                        "char_count": len(chunk_text)
                    }
                }
