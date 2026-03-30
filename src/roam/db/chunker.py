from bs4 import BeautifulSoup

# removes HTML tags from NPS API fields that contain markup
def _strip_html(text: str) -> str:
    if not text:
        return ""
    
    return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip()

# creates a chunk dict in the standard format
def _make_chunk(park_code: str, park_name: str, content_type: str,
                chunk_text: str, metadata: dict) -> dict:
    return {
        "park_code": park_code,
        "park_name": park_name,
        "content_type": content_type,
        "chunk_text": chunk_text.strip(),
        "metadata": metadata,
    }