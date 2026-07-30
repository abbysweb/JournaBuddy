"""
JournaBuddy OpenAlex API Client
Fetches author metrics (h-index, total citations) and paper citation counts
using the open, free OpenAlex index.
"""
import logging
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class OpenAlexClient:
    """Async client for the OpenAlex REST API."""

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout
        self.base_url = "https://api.openalex.org"
        self.headers = {"User-Agent": "JournaBuddy/2.0 (mailto:admin@journabuddy.local)"}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_work_by_doi(self, doi: str) -> Optional[dict]:
        """
        Fetch citation stats for a paper using its DOI.
        
        Args:
            doi: The DOI string.
            
        Returns:
            Dict containing citation_count and related concepts, or None.
        """
        # OpenAlex expects DOIs in the format https://doi.org/...
        clean_doi = doi.replace("https://doi.org/", "")
        url = f"{self.base_url}/works/https://doi.org/{clean_doi}"
        
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.get(url)
                
                if response.status_code == 404:
                    return None
                    
                response.raise_for_status()
                data = response.json()
                
                concepts = [c["display_name"] for c in data.get("concepts", []) if c["level"] <= 1]
                
                return {
                    "doi": doi,
                    "title": data.get("title", ""),
                    "citation_count": data.get("cited_by_count", 0),
                    "concepts": concepts[:5],
                }
        except Exception as e:
            logger.error(f"OpenAlex lookup failed for work {doi}: {e}")
            return None
