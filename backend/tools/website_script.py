import requests
from bs4 import BeautifulSoup
import re

def extract_text_from_url(url: str) -> str:
    """Scrape and extract text content from a given URL."""
    try:
        resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
            
        text = soup.get_text(separator='\n')
        
        # Collapse multiple newlines and spaces
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        return f"[Error extracting website content: {e}]"
