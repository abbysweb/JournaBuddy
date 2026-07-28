import requests
import urllib.parse
from typing import Dict, Any

def search_journal(journal_name: str) -> Dict[str, Any]:
    """Search for a journal by name using the OpenAlex API."""
    encoded_name = urllib.parse.quote(journal_name)
    url = f"https://api.openalex.org/sources?search={encoded_name}&per-page=1"
    
    default_result = {
        "found": False,
        "name": journal_name,
        "publisher": "Unknown",
        "h_index": 0,
        "impact_factor": 0.0,
        "open_access": False,
        "issn": [],
        "apc_usd": None,
        "homepage_url": None
    }

    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results:
                source = results[0]
                summary = source.get("summary_stats", {})
                
                return {
                    "found": True,
                    "name": source.get("display_name", journal_name),
                    "publisher": source.get("host_organization_name", "Unknown Publisher"),
                    "h_index": summary.get("h_index", 0),
                    "impact_factor": round(summary.get("2yr_mean_citedness", 0.0), 2),
                    "open_access": source.get("is_oa", False),
                    "issn": source.get("issn", []),
                    "apc_usd": source.get("apc_usd", None),
                    "homepage_url": source.get("homepage_url", None)
                }
    except Exception as e:
        print(f"[OpenAlex] Error fetching {journal_name}: {e}")
        
    return default_result
