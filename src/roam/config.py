from dotenv import load_dotenv
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
    "grca": "Grand Canyon National Park (Arizona)",
    "jotr": "Joshua Tree National Park (California)",
    "yose": "Yosemite National Park (California)",
    "romo": "Rocky Mountain National Park (Colorado)",
    "acad": "Acadia National Park (Maine)",
    "glac": "Glacier National Park (Montana)",
    "zion": "Zion National Park (Utah)",
    "olym": "Olympic National Park (Washington)",
    "yell": "Yellowstone National Park (Wyoming)",
    "grte": "Grand Teton National Park (Wyoming)",
}

PARKS_BY_STATE = {
    "Arizona": ["Grand Canyon National Park"],
    "California": ["Joshua Tree National Park", "Yosemite National Park"],
    "Colorado": ["Rocky Mountain National Park"],
    "Maine": ["Acadia National Park"],
    "Montana": ["Glacier National Park"],
    "Utah": ["Zion National Park"],
    "Washington": ["Olympic National Park"],
    "Wyoming": ["Yellowstone National Park", "Grand Teton National Park"],
}

# extracted park codes
TARGET_PARKS = list(PARK_METADATA.keys())