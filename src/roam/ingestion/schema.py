import psycopg2
from sqlalchemy import Connection, text

from roam.config import DATABASE_URL
from roam.db.engine import sync_engine

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
    return psycopg2.connect(DATABASE_URL)

def setup_schema():
    print(f"Connected to: {sync_engine.url.host}:{sync_engine.url.port}/{sync_engine.url.database}")

    with sync_engine.begin() as connection:
        connection.execute(text(CREATE_EXTENSION))
        connection.execute(text(CREATE_PARKS_TABLE))
        connection.execute(text(CREATE_CHUNKS_TABLE))
        for index_sql in CREATE_INDEXES:
            connection.execute(text(index_sql))

    print("Schema created successfully")

def clear_park_chunks(connection: Connection, park_code: str):
    connection.execute(
        text("DELETE FROM park_chunks WHERE park_code = :park_code"), 
        {"park_code": park_code},
    )

if __name__ == '__main__':
    setup_schema()