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

# chunks core park metadata into embeddable units
def chunk_park_info(park_info: dict) -> list[dict]:
    chunks = []
    park_code = park_info["park_code"]
    park_name = park_info["name"]

    # overview chunk with decription and designation
    if park_info.get("description"):
        text = f"{park_name}\n{park_info["designation"]}\n\n{park_info["description"]}"
        overview_chunk = _make_chunk(park_code, park_name, "park_info", text,
                            {"source": "nps_api", "section": "overview"})
        chunks.append(overview_chunk)
    
    # weather chunk
    if park_info.get("weather_info"):
        weather_chunk = _make_chunk(park_code, park_name, "park_info", park_info["weather_info"],
                            {"source": "nps_api", "section": "weather"})
        chunks.append(weather_chunk)
    
    # directions chunk
    if park_info.get("directions_info"):
        directions_chunk = _make_chunk(park_code, park_name, "park_info", park_info["directions_info"],
                            {"source": "nps_api", "section": "directions"})
        chunks.append(directions_chunk)

    # entrance fees chunk
    if park_info.get("entrance_fees"):
        lines = [f"{park_name} Entrance Fees"]

        for fee in park_info["entrance_fees"]:
            lines.append(f"- {fee.get('title', '')}: ${fee.get('cost', '')} — {fee.get('description', '')}")
        
        fees_chunk = _make_chunk(park_code, park_name, "park_info", "\n".join(lines),
                            {"source": "nps_api", "section": "entrance_fees"})
        chunks.append(fees_chunk)
    
    # activities chunk
    if park_info.get("activities"):
        text = f"{park_name} activities include: {", ".join(park_info["activities"])}."
        activities_chunk = _make_chunk(park_code, park_name, "park_info", text,
                                       {"source": "nps_api", "section": "activities"})
        chunks.append(activities_chunk)
    
    return chunks
    
# chunks alerts individually
def chunk_alerts(alerts: list[dict], park_code: str, park_name: str) -> list[dict]:
    chunks = []

    for alert in alerts:
        if not alert.get("title") and not alert.get("description"):
            continue

        text = f"[{alert.get("category", "Alert")}] {alert.get("title", "")}\n{alert.get("description", "")}"

        if alert.get("url"):
            text += f"\nMore info at: {alert["url"]}"
        
        alert_chunk = _make_chunk(park_code, park_name, "alert", text,
                                  {"source": "nps_api", "section": "alert", "category": alert.get("category")})
        chunks.append(alert_chunk)
    
    return chunks

# chunks each visitor center individually
def chunk_visitor_centers(visitor_centers: list[dict], park_code: str, park_name: str) -> list[dict]:
    chunks = []

    for vc in visitor_centers:
        if not vc.get("name"):
            continue

        lines = [f"{vc["name"]} - Visitor Center"]
        if vc.get("description"):
            lines.append(vc["description"])
        if vc.get("directions"):
            lines.append(f"Directions: {vc["directions"]}")
        if vc.get("amenities"):
            lines.append(f"Amenities: {vc["amenities"]}")
        if vc.get("operating_hours"):
            for hours in vc["operating_hours"]:
                lines.append(f"Hours: {hours["description"]}")
        
        vc_chunk = _make_chunk(park_code, park_name, "visitor_center", "\n".join(lines),
                               {"source": "nps_api", "section": "visitor_center", "name": vc["name"]})
        
        chunks.append(vc_chunk)
    
    return chunks