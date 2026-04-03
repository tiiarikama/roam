import re
from pathlib import Path

PARKS_DIR = Path(__file__).parent.parent.parent.parent / "parks"

MAX_CHUNK_CHARS = 2000

# reads .md file for a given park and splits into heading-based chunks. Initial split at ##, then recursively splits at ### ... if chunk is too large
def load_markdown_chunks(park_code: str) -> list[dict]:
    path = PARKS_DIR / f"{park_code}.md"

    if not path.exists():
        print(f"No markdown file found for {park_code}, skipping.")
        return []
    
    text = path.read_text(encoding="utf-8")
    park_name = _extract_park_name(text)
    chunks = _split_by_headings(text, park_code, park_name)
    return chunks

# extracts parks name from the # title heading
def _extract_park_name(text: str) -> str:
    match = re.search(r"^# (.+)", text, flags=re.MULTILINE)

    if not match:
        raise ValueError("Markdown file is missing a # title heading.")
    
    return match.group(1).strip()

# creates a chunk with metadata
def _make_chunk(park_code: str, park_name: str, heading: str,
                content: str, parent_heading: str = None) -> dict:
    if parent_heading:
        section = f"{parent_heading} > {heading}"
    else:
        section = heading
    
    return {
        "park_code": park_code,
        "park_name": park_name,
        "content_type": "markdown",
        "chunk_text": content.strip(),
        "metadata": {
            "source": "markdown",
            "section": section,
            "file": f"{park_code}.md"
        },
    }


# splits markdown text at a given subheading level (2, 3, or 4). Returns list of (heading, content) tuples
def _split_at_level(text: str, level: int) -> list[tuple[str, str]]:
    prefix = "#" * level + " "
    pattern = rf"(?=^{re.escape(prefix)})"
    sections = re.split(pattern, text, flags=re.MULTILINE)
    result = []

    for section in sections:
        section = section.strip()

        if not section:
            continue
        
        match = re.match(rf"^{re.escape(prefix)}(.+)", section)

        if not match:
            continue

        heading = match.group(1).strip()
        result.append((heading, section))
    
    return result


# splits markdown into chunks using a hybrid heading strategy based on chunk size: ## -> ### -> ####
def _split_by_headings(text: str, park_code: str, park_name: str) -> list[dict]:
    chunks = []

    # split at ##
    h2_sections = _split_at_level(text, 2)

    for h2_heading, h2_content in h2_sections:

        # if the chunk is already an appropriate length, add to chunks and continue
        if 50 <= len(h2_content) <= MAX_CHUNK_CHARS:
            chunk = _make_chunk(park_code, park_name, h2_heading, h2_content)
            chunks.append(chunk)
            continue

        # split oversized chunk at ### headings
        h3_sections = _split_at_level(h2_content, 3)

        # if no ### headings, add chunk as is
        if not h3_sections:
            chunk = _make_chunk(park_code, park_name, h2_heading, h2_content)
            chunks.append(chunk)
            continue

        for h3_heading, h3_content in h3_sections:
            if 50 <= len(h3_content) <= MAX_CHUNK_CHARS:
                chunk = _make_chunk(park_code, park_name, h3_heading, h3_content, parent_heading=h2_heading)
                chunks.append(chunk)
                continue
        
            # split oversized chunk at #### headings
            h4_sections = _split_at_level(h3_content, 4)

            # if no #### headings, add chunk as is
            if not h4_sections:
                chunk = _make_chunk(park_code, park_name, h3_heading, h3_content, parent_heading=h2_heading)
                chunks.append(chunk)
                continue

            # no upper bound check, the deepest level where heading is ####, stored as-is to not lose meaning
            for h4_heading, h4_content in h4_sections:
                if len(h4_content) >= 50:
                    chunk = _make_chunk(park_code, park_name, h4_heading, h4_content, parent_heading=f"{h2_heading} > {h3_heading}")
                    chunks.append(chunk)
        
    return chunks


