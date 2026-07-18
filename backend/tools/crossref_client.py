import re
import requests
from typing import List, Dict, Any

import requests
import urllib.parse
from typing import List, Dict, Any

def search_crossref_by_title(title: str) -> Dict[str, Any]:
    """Search for a paper by title using the Crossref API."""
    encoded_title = urllib.parse.quote(title)
    url = f"https://api.crossref.org/works?query.title={encoded_title}&select=DOI,title,published-print,published-online&rows=1"
    
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "ResearchGuardian/1.0 (mailto:mamun.swe.de@gmail.com)"})
        if resp.status_code == 200:
            data = resp.json().get("message", {})
            items = data.get("items", [])
            
            if items:
                item = items[0]
                found_title = item.get("title", [""])[0]
                doi = item.get("DOI", "")
                
                year = None
                if "published-print" in item:
                    year = item["published-print"].get("date-parts", [[None]])[0][0]
                elif "published-online" in item:
                    year = item["published-online"].get("date-parts", [[None]])[0][0]
                    
                citations_count = item.get("is-referenced-by-count", 0)
                return {"doi": doi, "found": True, "title": found_title, "year": year, "citations": citations_count}
            else:
                return {"doi": "", "found": False, "title": title, "year": None, "citations": 0}
        else:
            return {"doi": "", "found": False, "title": title, "year": None, "citations": 0}
    except Exception:
        return {"doi": "", "found": False, "title": title, "year": None, "citations": 0}

def validate_citations(citations: List[str]) -> Dict[str, Any]:
    """Validate a list of extracted citation titles against Crossref."""
    # Limit to first 10 for performance in demo
    citations_to_check = citations[:10]
    results = [search_crossref_by_title(c) for c in citations_to_check]
    
    found_count = sum(1 for r in results if r["found"])
    total_citations = sum(r.get("citations", 0) for r in results)
    total = len(results)
    coverage = (found_count / total * 100) if total > 0 else 0.0
    
    return {
        "dois": results,
        "total": total,
        "found": found_count,
        "coverage_percent": round(coverage, 1),
        "total_impact": total_citations,
        "avg_impact": round(total_citations / found_count, 1) if found_count > 0 else 0
    }
