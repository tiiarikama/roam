import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from roam.config import (
    EMBEDDING_MODEL, EMBEDDING_DIMENSIONS, TOP_K_RESULTS, SIMILARITY_THRESHOLD
)
from roam.db.engine import async_engine, format_vector
from roam.llm import async_client

# base similarity search query
SELECT_CHUNKS = """
    SELECT
        park_code,
        park_name,
        content_type,
        chunk_text,
        metadata,
        1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
    FROM park_chunks
    WHERE 1 - (embedding <=> CAST(:embedding AS vector)) > :threshold
"""

# added for park specific queries
PARK_FILTER = """
        AND park_code = :park_code
"""

ORDER_BY_SIMILARITY = """
    ORDER BY embedding <=> CAST(:embedding AS vector)
    LIMIT :top_k
"""

# embeds a user query using the same model as the stored chunks in knowledge base
async def embed_query(user_query: str) -> list[float]:
    response = await async_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[user_query],
        dimensions=EMBEDDING_DIMENSIONS,
    )

    return response.data[0].embedding

# retrieves the k most semantically similar chunks to a user query, when park code is None searches across all parks
async def retrieve(conn: AsyncConnection, query_embedding: list[float], park_code: str | None = None, top_k: int = TOP_K_RESULTS) -> list[dict]:
    sql_query = SELECT_CHUNKS + (PARK_FILTER if park_code else "") + ORDER_BY_SIMILARITY

    params = {
        "embedding": format_vector(query_embedding),
        "threshold": SIMILARITY_THRESHOLD,
        "top_k": top_k,
    }

    if park_code:
        params["park_code"] = park_code

    result = await conn.execute(text(sql_query), params)

    return [
        {
            "park_code": row.park_code,
            "park_name": row.park_name,
            "content_type": row.content_type,
            "chunk_text": row.chunk_text,
            "metadata": row.metadata,
            "similarity": round(row.similarity, 4),
        }
        for row in result
    ]

if __name__ == '__main__':
    test_queries = [
        ("What permits do I need to hike Half Dome?", "yose"),
        ("Where can I camp in Yosemite Valley?", "yose"),
        ("Which park has the best hiking?", None),
    ]

    async def main():
        async with async_engine.connect() as connection:
            for query, park_code in test_queries:
                print(f"\nQuery: {query} (park: {park_code or 'all'})")
                print("-" * 60)
                query_embedding = await embed_query(query)
                results = await retrieve(connection, query_embedding, park_code=park_code)
                for result in results[:3]:
                    print(f"  [{result['similarity']}] {result['park_code']} | {result['content_type']} | {result['metadata'].get('section', '')}")
                    print(f"  {result['chunk_text'][:150]}...")
                    print()

        await async_engine.dispose()

    asyncio.run(main())
