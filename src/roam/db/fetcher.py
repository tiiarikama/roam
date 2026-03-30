import requests
from roam.config import NPS_API_KEY, NPS_BASE_URL, TARGET_PARKS


# private, shared base request handler for NPS API 
def _nps_get(endpoint: str, params: dict) -> dict:
    params["api_key"] = NPS_API_KEY
    response = requests.get(f"{NPS_BASE_URL}/{endpoint}", params=params)
    response.raise_for_status()
    return response.json()

# endpoint handler for NPS API /parks: core park metadata and description
def fetch_park_info(park_code: str) -> dict:
    response = _nps_get("parks", {"parkCode": park_code, "limit": 1})

    if not response["data"]:
        raise ValueError(f"No park found for code: {park_code}")
    
    park_data = response["data"][0]

    return {
        "park_code": park_code,
        "name": park_data.get("fullName", ""),
        "description": park_data.get("description", ""),
        "states": park_data.get("states", ""),
        "designation": park_data.get("designation", ""),
        "weather_info": park_data.get("weatherInfo"),
        "directions_info": park_data.get("directionsInfo"),
        "activities": [activity["name"] for activity in park_data.get("activities", [])],
        "topics": [topic["name"] for topic in park_data.get("topics", [])],
        "entrance_fees": park_data.get("entranceFees", []),
        "operating_hours": park_data.get("operatingHours", []),
    }

# endpoint handler for NPS API /alerts: active alers (closures, hazards, notices)
def fetch_alerts(park_code: str) -> list[dict]:
    response = _nps_get("alerts", {"parkCode": park_code, "limit": 50})

    alerts = []

    for alert in response.get("data", []):
        alerts.append({
            "title": alert.get("title", ""),
            "description": alert.get("description", ""),
            "category": alert.get("category", ""),
            "url": alert.get("url", "")
        })
    
    return alerts