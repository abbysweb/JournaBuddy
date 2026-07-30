"""
JournaBuddy Crossref API Client
Verifies DOIs found in manuscripts against the official Crossref database.
Used to validate reference lists and ensure citations are real.
"""
import logging
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class CrossrefClient:
    """Async client for the Crossref REST API."""

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.base_url = "https://api.crossref.org/works"
        # Provide a mailto header as requested by Crossref polite pool guidelines
        self.headers = {"User-Agent": "JournaBuddy/2.0 (mailto:admin@journabuddy.local)"}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def verify_doi(self, doi: str) -> Optional[dict]:
        """
        Verify a DOI and fetch its metadata.
        
        Args:
            doi: The DOI string (e.g., "10.1038/nature12373")
            
        Returns:
            Dict containing title, publisher, and container-title (journal),
            or None if the DOI does not exist.
        """
        url = f"{self.base_url}/{doi}"
        
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.get(url)
                
                if response.status_code == 404:
                    return None
                    
                response.raise_for_status()
                data = response.json().get("message", {})
                
                return {
                    "doi": doi,
                    "title": data.get("title", [""])[0],
                    "publisher": data.get("publisher", ""),
                    "journal": data.get("container-title", [""])[0],
                    "is_valid": True,
                }
        except Exception as e:
            logger.error(f"Crossref lookup failed for {doi}: {e}")
            return None
