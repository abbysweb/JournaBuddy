import os
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer

QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = "journabuddy_chunks"

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
model = SentenceTransformer("all-MiniLM-L6-v2")

USE_QDRANT = False
_local_store = {} # task_id -> list of dicts with {"text": text, "vector": vector}

def initialize_vector_store():
    """Ensure the Qdrant collection exists on startup, with connection retries and error fallback."""
    global USE_QDRANT
    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Check if Qdrant is reachable
            if client.collection_exists(COLLECTION_NAME):
                print(f"[VectorStore] Qdrant collection '{COLLECTION_NAME}' already exists.")
            else:
                client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                print(f"[VectorStore] Created Qdrant collection: {COLLECTION_NAME}")
            USE_QDRANT = True
            return
        except Exception as e:
            print(f"[VectorStore] [Attempt {attempt + 1}/{max_retries}] Error connecting to Qdrant: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                print("[WARNING] [VectorStore] Failed to initialize Qdrant. Falling back to in-memory vector store.")
                USE_QDRANT = False

def index_chunks(task_id: str, chunks: list[str]):
    """Embeds and indexes a list of text chunks associated with a task_id."""
    if not chunks:
        return
        
    embeddings = model.encode(chunks).tolist()
    
    if USE_QDRANT:
        try:
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                points.append(PointStruct(
                    id=hash(f"{task_id}_{i}") % ((1<<63)-1),  # Qdrant accepts unsigned int64
                    vector=embedding,
                    payload={"task_id": task_id, "chunk_index": i, "text": chunk}
                ))
            client.upsert(collection_name=COLLECTION_NAME, points=points)
            print(f"[VectorStore] Indexed {len(points)} chunks for task {task_id} in Qdrant.")
            return
        except Exception as e:
            print(f"[VectorStore] Qdrant upsert failed ({e}). Falling back to local in-memory store.")

    # Local fallback
    _local_store[task_id] = []
    for chunk, embedding in zip(chunks, embeddings):
        _local_store[task_id].append({
            "text": chunk,
            "vector": embedding
        })
    print(f"[VectorStore] Indexed {len(chunks)} chunks in-memory for task {task_id}")

def search_chunks(task_id: str, query: str, top_k: int = 5) -> list[str]:
    """Semantic search for chunks related to a query within a specific task."""
    query_vector = model.encode(query).tolist()
    
    if USE_QDRANT:
        try:
            results = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                query_filter={
                    "must": [
                        {"key": "task_id", "match": {"value": task_id}}
                    ]
                },
                limit=top_k
            )
            return [hit.payload["text"] for hit in results]
        except Exception as e:
            print(f"[VectorStore] Qdrant search failed ({e}). Falling back to local in-memory search.")
            
    # Local fallback search using manual cosine similarity
    chunks_data = _local_store.get(task_id, [])
    if not chunks_data:
        return []
        
    import math
    def dot_product(v1, v2):
        return sum(x*y for x, y in zip(v1, v2))
    def magnitude(v):
        return math.sqrt(sum(x*x for x in v))
    def cosine_similarity(v1, v2):
        mag1 = magnitude(v1)
        mag2 = magnitude(v2)
        if mag1 == 0 or mag2 == 0:
            return 0
        return dot_product(v1, v2) / (mag1 * mag2)
        
    scored_chunks = []
    for item in chunks_data:
        score = cosine_similarity(query_vector, item["vector"])
        scored_chunks.append((score, item["text"]))
        
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    return [text for _, text in scored_chunks[:top_k]]
