import psycopg2
from openai import OpenAI
from roam.config import (
    OPENAI_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIMENSIONS, TOP_K_RESULTS
)
from roam.db.schema import connect

client = OpenAI(api_key=OPENAI_API_KEY)

# embeds a user query using the same model as the stored chunks in knowledge base
def embed_query(user_query: str) -> list[float]:
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[user_query],
        dimensions=EMBEDDING_DIMENSIONS,
    )

    return response.data[0].embedding

# retrieves the k most semantically similar chunks to a user query
def retrieve(user_query: str, park_code: str, top_k: int = TOP_K_RESULTS) -> list[dict]:
    query_embedding = embed_query(user_query)
    sql_query = """
                SELECT
                    park_code,
                    park_name,
                    content_type,
                    chunk_text,
                    metadata,
                    1 - (embedding <=> %s::vector) AS similarity
                FROM park_chunks
                WHERE park_code = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
    """

    connection = connect()
    try:
        with connection.cursor() as cur:
            cur.execute(sql_query, [query_embedding, park_code, query_embedding, top_k])
            rows = cur.fetchall()
            return [
                {
                    "park_code": row[0],
                    "park_name": row[1],
                    "content_type": row[2],
                    "chunk_text": row[3],
                    "metadata": row[4],
                    "similarity": round(row[5], 4),
                }
                for row in rows
            ]
    finally:
        connection.close()

if __name__ == '__main__':
    test_queries = [
        "What permits do I need to hike Half Dome?",
        "Are there road closures at Yosemite?",
        "Where can I camp in Yosemite Valley?",
        "What is the best time to see waterfalls?",
        "Is there cell service in the park?",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 60)
        results = retrieve(query, park_code="yose")
        for result in results[:3]:
            print(f"  [{result['similarity']}] {result['content_type']} | {result['metadata'].get('section', '')}")
            print(f"  {result['chunk_text'][:150]}...")
            print()

