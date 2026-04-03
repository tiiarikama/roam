import requests
from roam.config import PARK_METADATA
 
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

def _fetch_weather(park_code: str) -> dict | None:
    coordinates = PARK_METADATA.get(park_code, {}).get("coordinates")

    if not coordinates:
        return None
    
    latitude, longitude = coordinates

    try:
        response = requests.get(OPEN_METEO_URL, params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m,precipitation",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "timezone": "auto",
            "forecast_days": 7,
        })

        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Weather fetch error for {park_code}: {e}")
        return None


def _format_weather(park_code: str, data: dict) -> str:
    park_name = PARK_METADATA[park_code]["name"]
    current = data["current"]

    condition = WMO_CODES.get(current["weather_code"], "Unknown")
    lines = [
        f"Current conditions at {park_name}:",
        f"- {condition}, {current['temperature_2m']}°F (feels like {current['apparent_temperature']}°F)",
        f"- Wind: {current['wind_speed_10m']} mph",
        f"- Precipitation: {current['precipitation']} in",
        "",
        "7-day forecast:",
    ]

    daily = data["daily"]
    for i, date in enumerate(daily["time"]):
        code = daily["weather_code"][i]
        condition = WMO_CODES.get(code, "Unknown")
        high = daily["temperature_2m_max"][i]
        low = daily["temperature_2m_min"][i]
        precip = daily["precipitation_probability_max"][i]
        lines.append(f"- {date}: {condition}, {high}°F / {low}°F, {precip}% chance of precipitation")
 
    return "\n".join(lines)

def get_weather(park_code: str) -> str | None:
    data = _fetch_weather(park_code)
    
    if not data:
        return None
    
    return _format_weather(park_code, data)



if __name__ == "__main__":
    test_parks = ["yose", "grca", "acad"]
 
    for park in test_parks:
        print(f"\n{'=' * 60}")
        result = get_weather(park)
        if result:
            print(result)
        else:
            print(f"Failed to fetch weather for {park}")
 