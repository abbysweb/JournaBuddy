"""
JournaBuddy DOAJ API Client
Checks if a journal is indexed in the Directory of Open Access Journals (DOAJ).
Used for Module 3 (Journal Trust Scorer).
"""
import logging
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class DOAJClient:
    """Async client for the DOAJ REST API."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.base_url = "https://doaj.org/api/v3"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def check_journal(self, title_or_issn: str) -> dict:
        """
        Search DOAJ for a journal to check legitimacy.
        
        Args:
            title_or_issn: Journal title or ISSN.
            
        Returns:
            Dict with boolean is_doaj_indexed and trust_score modifier.
        """
        url = f"{self.base_url}/search/journals/{title_or_issn}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                results = data.get("results", [])
                if not results:
                    return {
                        "query": title_or_issn,
                        "is_doaj_indexed": False,
                        "trust_score": 0.0,
                    }
                
                best_match = results[0]["bibjson"]
                return {
                    "query": title_or_issn,
                    "is_doaj_indexed": True,
                    "trust_score": 10.0,  # DOAJ indexing is a strong trust signal
                    "journal_title": best_match.get("title", ""),
                    "publisher": best_match.get("publisher", {}).get("name", ""),
                    "subjects": [s.get("term") for s in best_match.get("subject", [])][:3],
                }
        except Exception as e:
            logger.error(f"DOAJ lookup failed for {title_or_issn}: {e}")
            return {
                "query": title_or_issn,
                "is_doaj_indexed": False,
                "trust_score": 0.0,
                "error": str(e),
            }
