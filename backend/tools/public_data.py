import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import os

def fetch_arxiv_papers(query: str, max_results: int = 5) -> list:
    """Fetch public domain papers from ArXiv API based on a search query."""
    url = f'http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query)}&start=0&max_results={max_results}'
    try:
        response = urllib.request.urlopen(url)
        data = response.read()
        
        root = ET.fromstring(data)
        
        # ArXiv XML namespace
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        papers = []
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
            published = entry.find('atom:published', ns).text
            link = entry.find('atom:id', ns).text
            
            papers.append({
                'title': title,
                'summary': summary,
                'published': published,
                'link': link
            })
            
        return papers
    except Exception as e:
        print(f"Error fetching from ArXiv: {e}")
        return []

def fetch_tu_wien_data(query: str, max_results: int = 5) -> list:
    """Fetch research data from TU Wien API using the configured token."""
    token = os.environ.get("TU_WIEN_API_TOKEN")
    if not token:
        print("TU_WIEN_API_TOKEN not set in environment.")
        return []
        
    url = f'https://researchdata.tuwien.ac.at/api/records?q={urllib.parse.quote(query)}&size={max_results}'
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Accept', 'application/json')
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        
        records = []
        for hit in data.get('hits', {}).get('hits', []):
            metadata = hit.get('metadata', {})
            title = metadata.get('title', 'Unknown Title')
            description = metadata.get('description', '')
            link = hit.get('links', {}).get('self', '')
            
            records.append({
                'title': title,
                'summary': description,
                'published': metadata.get('publication_date', 'Unknown'),
                'link': link
            })
            
        return records
    except Exception as e:
        print(f"Error fetching from TU Wien API: {e}")
        return []

def fetch_semantic_scholar(query: str, max_results: int = 5) -> list:
    """Fetch data from Semantic Scholar API."""
    url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query)}&limit={max_results}&fields=title,abstract,year,url'
    try:
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        
        records = []
        for item in data.get('data', []):
            records.append({
                'title': item.get('title', ''),
                'summary': item.get('abstract', ''),
                'published': str(item.get('year', '')),
                'link': item.get('url', '')
            })
        return records
    except Exception as e:
        print(f"Error fetching from Semantic Scholar: {e}")
        return []

def fetch_pubmed(query: str, max_results: int = 5) -> list:
    """Fetch from PubMed E-utilities API."""
    # First search to get IDs
    search_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={urllib.parse.quote(query)}&retmax={max_results}&retmode=json'
    try:
        search_res = urllib.request.urlopen(search_url)
        search_data = json.loads(search_res.read().decode('utf-8'))
        id_list = search_data.get('esearchresult', {}).get('idlist', [])
        
        if not id_list:
            return []
            
        # Then fetch summaries
        ids = ','.join(id_list)
        summary_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={ids}&retmode=json'
        sum_res = urllib.request.urlopen(summary_url)
        sum_data = json.loads(sum_res.read().decode('utf-8'))
        
        records = []
        for uid in id_list:
            item = sum_data.get('result', {}).get(uid, {})
            records.append({
                'title': item.get('title', ''),
                'summary': item.get('source', ''),
                'published': item.get('pubdate', ''),
                'link': f"https://pubmed.ncbi.nlm.nih.gov/{uid}/"
            })
        return records
    except Exception as e:
        print(f"Error fetching from PubMed: {e}")
        return []

def fetch_wikipedia(query: str) -> list:
    """Fetch summary from Wikipedia."""
    url = f'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&utf8=&format=json&srlimit=3'
    try:
        response = urllib.request.urlopen(url)
        data = json.loads(response.read().decode('utf-8'))
        
        records = []
        for item in data.get('query', {}).get('search', []):
            title = item.get('title', '')
            records.append({
                'title': title,
                'summary': item.get('snippet', '').replace('<span class="searchmatch">', '').replace('</span>', ''),
                'published': 'N/A',
                'link': f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
            })
        return records
    except Exception as e:
        print(f"Error fetching from Wikipedia: {e}")
        return []
