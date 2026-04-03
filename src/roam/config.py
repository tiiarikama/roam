from dotenv import load_dotenv
from collections import defaultdict
import os

load_dotenv()

# db
DATABASE_URL = os.getenv("DATABASE_URL")

# API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NPS_API_KEY = os.getenv("NPS_API_KEY")

# models
EMBEDDING_MODEL = 'text-embedding-3-small'
LLM_MODEL = "gpt-4o-mini"

# embedding
EMBEDDING_DIMENSIONS = 1536

# chunking
CHUNK_SIZE = 400
CHUNK_OVERLAP = 80

#routing
INTENT_CATEGORIES = ("park_specific", "comparative", "general_parks", "greeting", "off_topic")

# retrieval
TOP_K_RESULTS = 5
TOP_K_GLOBAL = 10

# NPS
NPS_BASE_URL = "https://developer.nps.gov/api/v1"

#available parks
PARK_METADATA = {
    "grca": {
        "name": "Grand Canyon National Park",
        "state": "Arizona",
        "coordinates": (36.1728, -112.6836),
    },
    "jotr": {
        "name": "Joshua Tree National Park",
        "state": "California",
        "coordinates": (33.8819, -115.9007),
    },
    "yose": {
        "name": "Yosemite National Park",
        "state": "California",
        "coordinates": (37.8488, -119.5572),
    },
    "romo": {
        "name": "Rocky Mountain National Park",
        "state": "Colorado",
        "coordinates": (40.3432, -105.6881),
    },
    "acad": {
        "name": "Acadia National Park",
        "state": "Maine",
        "coordinates": (44.3390, -68.2733),
    },
    "glac": {
        "name": "Glacier National Park",
        "state": "Montana",
        "coordinates": (48.6841, -113.8009),
    },
    "zion": {
        "name": "Zion National Park",
        "state": "Utah",
        "coordinates": (37.2978, -113.0288),
    },
    "olym": {
        "name": "Olympic National Park",
        "state": "Washington",
        "coordinates": (47.8039, -123.6664),
    },
    "yell": {
        "name": "Yellowstone National Park",
        "state": "Wyoming",
        "coordinates": (44.5982, -110.5472),
    },
    "grte": {
        "name": "Grand Teton National Park",
        "state": "Wyoming",
        "coordinates": (43.8185, -110.7055),
    },
}


PARKS_BY_STATE = defaultdict(list)
for data in PARK_METADATA.values():
    PARKS_BY_STATE[data["state"]].append(data["name"])


# extracted park codes
TARGET_PARKS = list(PARK_METADATA.keys())