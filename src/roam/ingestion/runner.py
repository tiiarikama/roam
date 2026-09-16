import json
import sys # for individual md file ingestion

from sqlalchemy import text, Connection

from roam.config import TARGET_PARKS
from roam.ingestion.schema import clear_park_chunks
from roam.db.engine import sync_engine, format_vector
from roam.ingestion.fetcher import fetch_all_park_data
from roam.ingestion.chunker import chunk_all
from roam.ingestion.md_loader import load_markdown_chunks
from roam.ingestion.embedder import embed_chunks

# inserts or updates a park record in the parks table
def upsert_park(connection: Connection, park_info: dict):
    sql_query = """
                INSERT INTO parks (park_code, name, description, states, designation)
                VALUES (:park_code, :name, :description, :states, :designation)
                ON CONFLICT (park_code) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    states = EXCLUDED.states,
                    designation = EXCLUDED.designation
    """

    connection.execute(text(sql_query), {
        "park_code": park_info["park_code"],
        "name": park_info["name"],
        "description": park_info["description"],
        "states": park_info["states"],
        "designation": park_info["designation"]
    })

# bulk inserts embedded chunks into park_chunks table
def insert_chunks(connection, chunks: list[dict]):
    if not chunks:
        return
    
    sql_query = """
                INSERT INTO park_chunks (park_code, park_name, content_type, chunk_text, metadata, embedding)
                VALUES (:park_code, :park_name, :content_type, :chunk_text, CAST(:metadata AS jsonb), CAST(:embedding AS vector))
    """

    connection.execute(text(sql_query), [
        {
            "park_code": chunk["park_code"],
            "park_name": chunk["park_name"],
            "content_type": chunk["content_type"],
            "chunk_text": chunk["chunk_text"],
            "metadata": json.dumps(chunk["metadata"]),
            "embedding": format_vector(chunk["embedding"]),
        }
        for chunk in chunks
    ])

# full ingestion pipeline for a single park
def run_park(park_code: str):
    print(f"\nProcessing {park_code}...")

    try:
        # fetch
        park_data = fetch_all_park_data(park_code)

        # chunk
        api_chunks = chunk_all(park_data)
        md_chunks = load_markdown_chunks(park_code)
        all_chunks = api_chunks + md_chunks
        print(f"Chunks: {len(api_chunks)} API + {len(md_chunks)} markdown = {len(all_chunks)} total")

        # embed
        embedded_chunks = embed_chunks(all_chunks)

        #store
        with sync_engine.begin() as connection:
            clear_park_chunks(connection, park_code)
            upsert_park(connection, park_data["park_info"])
            insert_chunks(connection, embedded_chunks)

        print(f"Stored {len(embedded_chunks)} chunks for {park_code}")
    except Exception as e:
        print(f"Error occurred processing {park_code}: {e}")
        raise

# full ingestion pipeline for all target parks
def run_all():
    print(f"Starting ingestion for {len(TARGET_PARKS)} parks...")
    success = []
    failed = []

    for park_code in TARGET_PARKS:
        try:
            run_park(park_code)
            success.append(park_code)
        except Exception as e:
            failed.append(park_code)
            print(e)

    print(f"\nIngestion complete.")
    print(f"Success: {success}")
    if failed:
        print(f"Failed:  {failed}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_park(sys.argv[1])
    else: run_all()