import os

def extract_text(file_path: str) -> str:
    """Extract all text from a PDF file using pypdf or PyMuPDF as a fallback."""
    # Try pypdf first since it is pure Python and doesn't suffer from DLL load failures on Windows
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
        return "\n".join(text_parts)
    except Exception as e1:
        # Fallback to PyMuPDF
        try:
            import fitz
            doc = fitz.open(file_path)
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
            return "\n".join(text_parts)
        except Exception as e2:
            return f"[Error extracting PDF: pypdf error: {e1}, PyMuPDF fallback also failed: {e2}]"

import io
def extract_text_from_bytes(file_bytes: bytes) -> str:
    """Extract all text from a PDF in-memory using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        text_parts = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
        return "\n".join(text_parts)
    except Exception as e:
        return f"[Error extracting PDF from bytes: {e}]"
