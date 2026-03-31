import psycopg2
from openai import OpenAI
from roam.config import (
    OPENAI_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIMENSIONS, TOP_K_RESULTS
)
from roam.db.schema import connect

client = OpenAI(api_key=OPENAI_API_KEY)

# embeds a user query using the same model as the stored chunks in knowledge base
def embed_query(query: str) -> list[float]:
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[query],
        dimensions=EMBEDDING_DIMENSIONS,
    )

    return response.data[0].embedding