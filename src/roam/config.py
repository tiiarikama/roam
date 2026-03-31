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

#available parks
PARK_METADATA = {
    "yose": "Yosemite National Park, California",
    "grca": "Grand Canyon National Park, Arizona",
    "zion": "Zion National Park, Utah",
    "olym": "Olympic National Park, Washington",
    "romo": "Rocky Mountain National Park, Colorado",
    "acad": "Acadia National Park, Maine",
    "yell": "Yellowstone National Park, Wyoming",
    "grte": "Grand Teton National Park, Wyoming",
    "jotr": "Joshua Tree National Park, California",
    "glac": "Glacier National Park, Montana",
}

# extracted park codes
TARGET_PARKS = list(PARK_METADATA.keys())