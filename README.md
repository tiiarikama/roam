# Roam

A national parks trip planning chatbot powered by RAG (Retrieval-Augmented Generation).
Ask about trails, permits, weather, and get help planning itineraries across 10 US national parks.

## Tech stack
- **RAG**: LangChain + pgvector
- **Embeddings**: OpenAI text-embedding-3-small
- **LLM**: Anthropic Claude
- **Backend**: FastAPI
- **Frontend**: Streamlit
- **Database**: PostgreSQL + pgvector

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
createdb national_parks_rag
python -m ingestion.schema
```

### 5. Run ingestion
```bash
# Ingest all parks
python -m ingestion.runner

# Or test with a single park first
python -m ingestion.runner yose
```

### 6. Run the app
```bash
streamlit run app/main.py
```

## Project structure
```
roam/
├── parks/          # Hand-curated markdown park documents
├── ingestion/      # Data pipeline: fetch → chunk → embed → store
├── rag/            # Retrieval layer: query router, retriever, chain
└── app/            # Streamlit frontend
```

## Data sources
- [NPS API](https://www.nps.gov/subjects/developer/index.htm) — park info, alerts, visitor centers
- Hand-curated markdown docs — trails, permits, seasonal access