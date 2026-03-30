from bs4 import BeautifulSoup

# removes HTML tags from NPS API fields that contain markup
def _strip_html(text: str) -> str:
    if not text:
        return ""
    
    return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip()
