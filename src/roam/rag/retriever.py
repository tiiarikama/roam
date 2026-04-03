import psycopg2
from openai import OpenAI
from roam.config import (
    OPENAI_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIMENSIONS, TOP_K_RESULTS
)
from roam.ingestion.schema import connect

client = OpenAI(api_key=OPENAI_API_KEY)

# embeds a user query using the same model as the stored chunks in knowledge base
def embed_query(user_query: str) -> list[float]:
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[user_query],
        dimensions=EMBEDDING_DIMENSIONS,
    )

    return response.data[0].embedding

# retrieves the k most semantically similar chunks to a user query, when park code is None searches across all parks
def retrieve(user_query: str, park_code: str = None, top_k: int = TOP_K_RESULTS) -> list[dict]:
    query_embedding = embed_query(user_query)

    if park_code:     
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
        params = [query_embedding, park_code, query_embedding, top_k]
    else:
        sql_query = """
                    SELECT
                        park_code,
                        park_name,
                        content_type,
                        chunk_text,
                        metadata,
                        1 - (embedding <=> %s::vector) AS similarity
                    FROM park_chunks
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
        """
        params = [query_embedding, query_embedding, top_k]

    connection = connect()
    try:
        with connection.cursor() as cur:
            cur.execute(sql_query, params)
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
        ("What permits do I need to hike Half Dome?", "yose"),
        ("Where can I camp in Yosemite Valley?", "yose"),
        ("Which park has the best hiking?", None),
    ]

    for query, park_code in test_queries:
        print(f"\nQuery: {query} (park: {park_code or 'all'})")
        print("-" * 60)
        results = retrieve(query, park_code=park_code)
        for result in results[:3]:
            print(f"  [{result['similarity']}] {result['park_code']} | {result['content_type']} | {result['metadata'].get('section', '')}")
            print(f"  {result['chunk_text'][:150]}...")
            print()
