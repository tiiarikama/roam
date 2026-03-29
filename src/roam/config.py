from dotenv import load_dotenv
import os

load_dotenv()

# db
DATABASE_URL = os.getenv("DATABASE_URL")

# API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NPS_API_KEY = os.getenv("NPS_API_KEY")

# embedding

EMBEDDING_MODEL = 'text-embedding-3-small'
EMBEDDING_DIMENSIONS = 1536

# chunking
CHUNK_SIZE = 400
CHUNK_OVERLAP = 80

# retrieval
TOP_K_RESULTS = 5

# NPS
NPS_BASE_URL = "https://developer.nps.gov/api/v1"

# available parks
TARGET_PARKS = [
    "yose",  # Yosemite
    "grca",  # Grand Canyon
    "zion",  # Zion
    "olym",  # Olympic
    "romo",  # Rocky Mountain
    "acad",  # Acadia
    "yell",  # Yellowstone
    "grte",  # Grand Teton
    "jotr",  # Joshua Tree
    "glac",  # Glacier
]