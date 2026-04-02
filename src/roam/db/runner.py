import json
import sys # for individual md file ingestion
import psycopg2
from roam.config import TARGET_PARKS
from roam.db.schema import connect, clear_park_chunks
from roam.db.fetcher import fetch_all_park_data
from roam.db.chunker import chunk_all
from roam.db.md_loader import load_markdown_chunks
from roam.db.embedder import embed_chunks

# inserts or updates a park record in the parks table
def upsert_park(connection, park_info: dict):
    sql_query = """
                INSERT INTO parks (park_code, name, description, states, designation)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (park_code) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    states = EXCLUDED.states,
                    designation = EXCLUDED.designation
    """

    with connection.cursor() as cur:
        cur.execute(sql_query, (
            park_info["park_code"],
            park_info["name"],
            park_info["description"],
            park_info["states"],
            park_info["designation"]
        ))

# bulk inserts embedded chunks into park_chunks table
def insert_chunks(connection, chunks: list[dict]):
    sql_query = """
                INSERT INTO park_chunks (park_code, park_name, content_type, chunk_text, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
    """

    with connection.cursor() as cur:
        for chunk in chunks:
            cur.execute(sql_query, (
                chunk["park_code"],
                chunk["park_name"],
                chunk["content_type"],
                chunk["chunk_text"],
                json.dumps(chunk["metadata"]),
                chunk["embedding"],   
            ))

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
        connection = connect()
        try:
            clear_park_chunks(park_code)
            upsert_park(connection, park_data["park_info"])
            insert_chunks(connection, embedded_chunks)
            connection.commit()
            print(f"Stored {len(embedded_chunks)} chunks for {park_code}")
        finally:
            connection.close()
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

    print(f"\nIngestion complete.")
    print(f"Success: {success}")
    if failed:
        print(f"Failed:  {failed}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_park(sys.argv[1])
    else: run_all()