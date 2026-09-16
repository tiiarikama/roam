import time
import math

from roam.config import EMBEDDING_MODEL, EMBEDDING_DIMENSIONS
from roam.llm import sync_client

BATCH_SIZE = 100
RATE_LIMIT_DELAY = 0.5

# generates embeddings for a list of chunks: processes in batches for API rate limiting. Returns same chunks with an added embedding key
def embed_chunks(chunks: list[dict]) -> list[dict]:
    if not chunks:
        return []
    
    total_batches = math.ceil(len(chunks) / BATCH_SIZE)
    print(f"Embedding {len(chunks)} chunks in {total_batches} batch(es)...")
    embedded = []

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i: i + BATCH_SIZE]
        texts = [chunk["chunk_text"] for chunk in batch]

        response = sync_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts,
            dimensions=EMBEDDING_DIMENSIONS,
        )

        for chunk, embedding_data in zip(batch, response.data):
            embedded.append({
                **chunk,
                "embedding": embedding_data.embedding,
            })
        
        current_batch = i // BATCH_SIZE + 1
        print(f"Embedded batch {current_batch} / {total_batches}")

        if i + BATCH_SIZE < len(chunks):
            time.sleep(RATE_LIMIT_DELAY)
    
    return embedded
