import os
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer

QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = "journabuddy_chunks"

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
model = SentenceTransformer("all-MiniLM-L6-v2")

def initialize_vector_store():
    """Ensure the Qdrant collection exists on startup, with connection retries and error fallback."""
    import time
    max_retries = 5
    for attempt in range(max_retries):
        try:
            if not client.collection_exists(COLLECTION_NAME):
                client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                print(f"[VectorStore] Created Qdrant collection: {COLLECTION_NAME}")
            else:
                print(f"[VectorStore] Qdrant collection '{COLLECTION_NAME}' already exists.")
            return
        except Exception as e:
            print(f"[VectorStore] [Attempt {attempt + 1}/{max_retries}] Error connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                print("[WARNING] [VectorStore] Failed to initialize Qdrant. Semantic search features will fail until Qdrant is available.")

def index_chunks(task_id: str, chunks: list[str]):
    """Embeds and indexes a list of text chunks associated with a task_id."""
    if not chunks:
        return
        
    embeddings = model.encode(chunks).tolist()
    
    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        points.append(PointStruct(
            id=hash(f"{task_id}_{i}") % ((1<<63)-1),  # Qdrant accepts unsigned int64
            vector=embedding,
            payload={"task_id": task_id, "chunk_index": i, "text": chunk}
        ))
        
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"[VectorStore] Indexed {len(points)} chunks for task {task_id}")

def search_chunks(task_id: str, query: str, top_k: int = 5) -> list[str]:
    """Semantic search for chunks related to a query within a specific task."""
    query_vector = model.encode(query).tolist()
    
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
