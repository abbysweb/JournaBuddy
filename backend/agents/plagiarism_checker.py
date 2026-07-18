import os
import requests
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# Initialize the model (lazy load to prevent slowing down imports)
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def chunk_text(text, max_words=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunks.append(" ".join(words[i:i+max_words]))
    return chunks

def search_duckduckgo(query):
    url = "https://html.duckduckgo.com/html/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        # Use first 30 words for search query
        search_query = " ".join(query.split()[:30])
        res = requests.post(url, data={'q': search_query}, headers=headers, timeout=10)
        if res.status_code != 200:
            return ""
        soup = BeautifulSoup(res.text, 'html.parser')
        results = soup.find_all('a', class_='result__snippet')
        snippets = [r.get_text(strip=True) for r in results]
        return " ".join(snippets)
    except Exception as e:
        print(f"[PlagiarismChecker] Search error: {e}")
        return ""

def run(raw_text: str) -> dict:
    """Run the plagiarism checker agent."""
    text_chunks = chunk_text(raw_text)
    if not text_chunks:
        return {"plagiarism_score": 0, "flagged_sentences": [], "verdict": "Original"}
    
    # To maintain performance, sample the longest chunks for web verification
    sorted_chunks = sorted(text_chunks, key=len, reverse=True)
    target_chunks = sorted_chunks[:5]
    
    flagged = []
    max_similarity = 0
    model = get_model()
    
    for chunk in target_chunks:
        if len(chunk.split()) < 10:
            continue
            
        online_text = search_duckduckgo(chunk)
        if not online_text:
            continue
            
        # 1. Structural Similarity (TF-IDF)
        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform([chunk, online_text])
            struct_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except ValueError:
            struct_sim = 0
            
        # 2. Semantic Similarity (BERT)
        embeddings = model.encode([chunk, online_text])
        sem_sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        
        sim_score = max(struct_sim, sem_sim)
        max_similarity = max(max_similarity, sim_score)
        
        if sim_score > 0.65:
            flagged.append({
                "text": chunk,
                "score": float(sim_score),
                "type": "Direct Copy" if struct_sim > 0.65 else "Paraphrased (Online)",
                "source": "Internet (DuckDuckGo)"
            })
            
    verdict = "Original"
    if max_similarity > 0.65:
        verdict = "Plagiarized"
    elif max_similarity > 0.3:
        verdict = "Suspicious / Heavily Paraphrased"
        
    return {
        "plagiarism_score": float(max_similarity),
        "flagged_sentences": flagged,
        "verdict": verdict
    }
