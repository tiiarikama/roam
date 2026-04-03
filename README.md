<p align="center">
  <img src="static/logo.svg" alt="Roam" width="500">
</p>

Roam - A national parks trip planning chatbot powered by RAG (Retrieval-Augmented Generation).
Ask about trails, permits, weather and more to get help planning itineraries across US national parks.

## Tech stack

- **Embeddings**: OpenAI text-embedding-3-small
- **LLM**: OpenAI gpt-4o-mini
- **Vector DB**: PostgreSQL + pgvector
- **Frontend**: Streamlit
- **Dependency Management**: Poetry
- **Python**: 3.12

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/yourusername/roam.git
cd roam
poetry install
```

### 2. Activate the environment

```bash
source $(poetry env info --path)/bin/activate
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys and database URL
```

### 4. Set up the database

```bash
createdb roam_dev
python -m roam.ingestion.schema
```

### 5. Run ingestion

```bash
# Ingest all parks
python -m roam.ingestion.runner

# Or test with a single park first
python -m roam.ingestion.runner yose
```

### 6. Run the app

```bash
streamlit run src/roam/app/main.py
```

## Project structure

```
roam/
├── .env.example
├── .gitignore
├── poetry.lock
├── pyproject.toml
├── README.md
├── static/                       # Logo and favicon
│   ├── logo.svg
│   └── favicon.png
├── parks/                        # Hand-curated markdown park documents
│   ├── acad.md
|   ├── glac.md
|   ├── grca.md
|   ├── grte.md
|   ├── jotr.md
|   ├── olym.md
|   ├── romo.md
|   ├── yell.md
|   ├── yose.md
|   └── zion.md
├── src/
│   └── roam/
│       ├── __init__.py
│       ├── config.py
│       ├── app/                   # Streamlit frontend
│       |    ├── __init__.py
│       |    └── main.py
│       ├── ingestion/             # Data pipeline: fetch → chunk → embed → store
│       │   ├── __init__.py
│       │   ├── schema.py
│       │   ├── fetcher.py
│       │   ├── chunker.py
│       │   ├── embedder.py
│       │   ├── md_loader.py
│       │   └── runner.py
│       ├── rag/                   # Retrieval layer: query router, retriever, chain
│       │   ├── __init__.py
│       │   ├── router.py
│       │   ├── retriever.py
│       │   └── chain.py
|       └── weather/               # Open-Meteo API client module for live weather data
|            └── client.py
└── tests/
    ├── __init__.py
    ├── test_chunker.py
    └── test_retriever.py
```

## Data sources

- [NPS API](https://www.nps.gov/subjects/developer/index.htm) — park info, alerts, visitor centers, campgrounds
- Hand-curated markdown docs — trails, permits, seasonal access, practical tips
