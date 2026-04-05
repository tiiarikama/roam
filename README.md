<p align="center">
  <img src="static/logo.svg" alt="Roam" width="500">
</p>

Roam — a national parks trip planning chatbot powered by RAG (Retrieval-Augmented Generation).
Ask about trails, permits, weather, and more to plan trips across US national parks.

## Tech Stack

- **LLM**: OpenAI gpt-4o-mini
- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- **Vector DB**: PostgreSQL + pgvector
- **Weather**: Open-Meteo API (live forecasts)
- **Park Data**: NPS API + hand-curated markdown
- **Frontend**: Streamlit
- **Package Management**: Poetry
- **Python**: 3.12

## Architecture

Roam uses a hybrid RAG pipeline with LLM-based query routing, semantic retrieval over a pgvector knowledge base, and optional live weather augmentation. At a high level:

1. An LLM-based **router** classifies each query by intent (`park_specific`, `comparative`, `general_parks`, `greeting`, `off_topic`), detects relevant park codes, and determines whether live weather is needed. Conversation context is injected so follow-ups like "what about camping there?" resolve correctly.
2. The **retriever** runs cosine similarity search against pgvector, filtering by park code for park-specific queries or searching globally for comparative/general non-park-specific ones.
3. The **chain** assembles retrieved chunks (and optionally a live weather forecast) into a context prompt and streams the LLM response.

The knowledge base is populated by an **ingestion pipeline** that merges two sources: structured data from the NPS API (alerts, campgrounds, visitor centers, fees) and hand-curated markdown files (trails, permits, seasonal tips). API data is chunked by domain entity; markdown is split by heading hierarchy with a 2000-char ceiling, preserving parent heading context in metadata.

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
```

Required environment variables:

| Variable         | Description                                                                                     |
| ---------------- | ----------------------------------------------------------------------------------------------- |
| `DATABASE_URL`   | PostgreSQL connection string                                                                    |
| `OPENAI_API_KEY` | OpenAI API key                                                                                  |
| `NPS_API_KEY`    | NPS Developer API key ([register here](https://www.nps.gov/subjects/developer/get-started.htm)) |

### 4. Set up the database

```bash
createdb roam_dev
python -m roam.ingestion.schema
```

### 5. Run ingestion

```bash
# Ingest all parks
python -m roam.ingestion.runner

# Or test with a single park
python -m roam.ingestion.runner yose
```

Running ingestion for a park clears its existing chunks before re-inserting.

### 6. Run the app

```bash
streamlit run src/roam/app/main.py
```

## Project Structure

```
roam/
├── .env.example
├── pyproject.toml
├── static/                        # Logo, favicon, and styles
├── parks/                         # Hand-curated markdown park documents
│   ├── acad.md
│   ├── glac.md
│   ├── grca.md
│   ├── grte.md
│   ├── jotr.md
│   ├── olym.md
│   ├── romo.md
│   ├── yell.md
│   ├── yose.md
│   └── zion.md
├── src/
│   └── roam/
│       ├── config.py              # API keys, model params, park metadata
│       ├── app/
│       │   └── main.py            # Streamlit chat interface
│       ├── ingestion/
│       │   ├── schema.py          # DB schema and connection helpers
│       │   ├── fetcher.py         # NPS API client
│       │   ├── chunker.py         # Domain-specific chunking for API data
│       │   ├── embedder.py        # Batched OpenAI embedding
│       │   ├── md_loader.py       # Heading-based markdown splitter
│       │   └── runner.py          # Ingestion orchestrator
│       ├── rag/
│       │   ├── router.py          # LLM-based intent classifier
│       │   ├── retriever.py       # pgvector similarity search
│       │   └── chain.py           # RAG orchestration: route → retrieve → generate
│       └── weather/
│           └── client.py          # Open-Meteo forecast client
└── tests/
```

## Data Sources

- **[NPS API](https://www.nps.gov/subjects/developer/index.htm)** — park info, alerts, visitor centers, campgrounds
- **Hand-curated markdown** — trails, permits, seasonal access, practical tips
- **[Open-Meteo API](https://open-meteo.com/)** — live current conditions and 7-day forecasts
