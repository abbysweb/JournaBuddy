import pdfplumber
import io

def extract_text_from_pdf(file_data: bytes) -> str:
    """Extracts raw text from PDF bytes using pdfplumber."""
    text_content = []
    
    # Use io.BytesIO to treat bytes as a file
    with pdfplumber.open(io.BytesIO(file_data)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_content.append(page_text)
                
    return "\n\n".join(text_content)
