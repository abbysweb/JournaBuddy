import re

def semantic_chunk_text(text: str, max_chunk_size: int = 1500, overlap: int = 200) -> list[str]:
    """
    Splits text into semantic chunks based on paragraphs, aiming for roughly `max_chunk_size` characters,
    with an overlap to preserve context between chunks.
    """
    # Simple semantic splitting by double newlines (paragraphs)
    paragraphs = re.split(r'\n\s*\n', text)
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # If adding the paragraph exceeds chunk size, save current and start new
        if len(current_chunk) + len(para) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Start next chunk with the overlap from the end of the previous chunk
            current_chunk = current_chunk[-overlap:] + " " + para if overlap < len(current_chunk) else para
        else:
            current_chunk += " " + para if current_chunk else para
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

def extract_and_chunk_pdf(raw_text: str) -> list[str]:
    """
    Takes raw PDF text, cleans it slightly, and chunks it semantically.
    """
    # Clean up excessive whitespace or weird PDF artifacts
    cleaned_text = re.sub(r'\s+', ' ', raw_text)
    
    # Split into sentences or rough chunks (since \n\n might be lost in simple PDF extraction)
    # A better approach for raw PDF text with lost newlines is chunking by sentence or fixed length
    sentences = re.split(r'(?<=[.!?]) +', cleaned_text)
    
    chunks = []
    current_chunk = ""
    max_chunk_size = 1500
    overlap = 200
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = current_chunk[-overlap:] + " " + sentence if overlap < len(current_chunk) else sentence
        else:
            current_chunk += " " + sentence if current_chunk else sentence
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks
