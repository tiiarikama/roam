import requests
from roam.config import NPS_API_KEY, NPS_BASE_URL


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

# endpoint handler for NPS API /visitorcenters: visitor center info including hours
def fetch_visitor_centers(park_code: str) -> list[dict]:
    response = _nps_get("visitorcenters", {"parkCode": park_code, "limit": 20})

    centers = []

    for center in response.get("data", []):
        centers.append({
            "name": center.get("name", ""),
            "description": center.get("description"),
            "directions": center.get("directionsInfo"),
            "amenities": center.get("amenities", []),
            "operating_hours": center.get("operatingHours", []),
        })
    
    return centers

# endpoint handler for NPS API /campgrounds: campground info including amenities, fees, and reservation details
def fetch_campgrounds(park_code: str) -> list[dict]:
    response = _nps_get("campgrounds", {"parkCode": park_code, "limit": 50})

    campgrounds = []

    for campground in response.get("data", []):
        campgrounds.append({
            "name": campground.get("name", ""),
            "description": campground.get("description"),
            "latitude": campground.get("latitude"),
            "longitude": campground.get("longitude"),
            "reservation_info": campground.get("reservationInfo"),
            "reservation_url": campground.get("reservationUrl"),
            "fees": campground.get("fees", []),
            "amenities": campground.get("amenities", {}),
            "campsites": campground.get("campsites", {}),
            "operating_hours": campground.get("operatingHours", []),
            "rv_allowed": campground.get("accessibility", {}).get("rvAllowed"),
            "rv_max_length": campground.get("accessibility", {}).get("rvMaxLength"),
        })
    
    return campgrounds

# all NPS API endpoint data for a given park
def fetch_all_park_data(park_code: str) -> dict:
    print(f"Fetching data for: {park_code}...")

    return {
        "park_info": fetch_park_info(park_code),
        "alerts": fetch_alerts(park_code),
        "visitor_centers": fetch_visitor_centers(park_code),
        "campgrounds": fetch_campgrounds(park_code),
    }