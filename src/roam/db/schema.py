import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

CREATE_EXTENSION = "CREATE EXTENSION IF NOT EXISTS vector;"

CREATE_PARKS_TABLE = """
CREATE TABLE IF NOT EXISTS parks (
    id          SERIAL PRIMARY KEY,
    park_code   VARCHAR(10) UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    description TEXT,
    states      TEXT,
    designation TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
"""

CREATE_CHUNKS_TABLE = """
CREATE TABLE IF NOT EXISTS park_chunks  (
    id              SERIAL PRIMARY KEY,
    park_code       VARCHAR(10) NOT NULL,
    park_name       TEXT NOT NULL,
    content_type    VARCHAR(50) NOT NULL,
    chunk_text      TEXT NOT NULL,
    metadata        JSONB DEFAULT '{}',
    embedding       vector(1536),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (park_code) REFERENCES parks(park_code)
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_chunks_park_code ON park_chunks(park_code);",
    "CREATE INDEX IF NOT EXISTS idx_chunks_content_type ON park_chunks(content_type);",
    "CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON park_chunks USING GIN(metadata);",
    "CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON park_chunks USING hnsw (embedding vector_cosine_ops);",
]

def connect():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def setup_schema():
    connection = connect()
    print(f"Connected to: {os.getenv('DATABASE_URL')}")

    try:
        with connection.cursor() as cur:
            cur.execute(CREATE_EXTENSION)
            cur.execute(CREATE_PARKS_TABLE)
            cur.execute(CREATE_CHUNKS_TABLE)
            for index_sql in CREATE_INDEXES:
                cur.execute(index_sql)

        connection.commit()
        print("Schema created successfully")
    finally:
        connection.close()

def clear_park_chunks(connection: psycopg2.extensions.connection, park_code: str):
    with connection.cursor() as cur:
        cur.execute(
            "DELETE FROM park_chunks WHERE park_code = %s", (park_code,)
        )

if __name__ == '__main__':
    setup_schema()