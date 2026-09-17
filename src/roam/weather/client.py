import httpx
import asyncio

from dataclasses import dataclass, field

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

QUERY_PARAMS = {
    "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m,precipitation",
    "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
    "temperature_unit": "fahrenheit",
    "wind_speed_unit": "mph",
    "timezone": "auto",
    "forecast_days": 7,
}

REQUEST_TIMEOUT = 8.0

@dataclass
class WeatherReport:
    park_code: str
    park_name: str
    prompt_text: str
    current: dict
    daily: list[dict] = field(default_factory=list)

    # data the API sends to UI to display, prose not needed
    def to_dict(self) -> dict:
        return {
            "park_code": self.park_code,
            "park_name": self.park_name,
            "current": self.current,
            "daily": self.daily,
        }

async def _fetch_weather(client, park_code: str) -> dict | None:
    coordinates = PARK_METADATA.get(park_code, {}).get("coordinates")

    if not coordinates:
        return None
    
    latitude, longitude = coordinates

    try:
        response = await client.get(OPEN_METEO_URL, params={**QUERY_PARAMS,
            "latitude": latitude,
            "longitude": longitude,
        },
        timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Weather fetch error for {park_code}: {e}")
        return None

# builds both weather renderings: structured data for the UI, prose for the prompt
def _build_report(park_code: str, data: dict) -> WeatherReport:
    park_name = PARK_METADATA[park_code]["name"]
    raw_current = data["current"]

    current = {
        "condition": WMO_CODES.get(raw_current["weather_code"], "Unknown"),
        "weather_code": raw_current["weather_code"],
        "temperature": raw_current["temperature_2m"],
        "apparent_temperature": raw_current["apparent_temperature"],
        "wind_speed": raw_current["wind_speed_10m"],
        "precipitation": raw_current["precipitation"],
    }

    raw_daily = data["daily"]
    daily = [
        {
            "date": date,
            "condition": WMO_CODES.get(raw_daily["weather_code"][index], "Unknown"),
            "weather_code": raw_daily["weather_code"][index],
            "high": raw_daily["temperature_2m_max"][index],
            "low": raw_daily["temperature_2m_min"][index],
            "precipitation_chance": raw_daily["precipitation_probability_max"][index],
        }
        for index, date in enumerate(raw_daily["time"])
    ]

    lines = [
        f"Current conditions at {park_name}:",
        f"- {current['condition']}, {current['temperature']}°F (feels like {current['apparent_temperature']}°F)",
        f"- Wind: {current['wind_speed']} mph",
        f"- Precipitation: {current['precipitation']} in",
        "",
        "7-day forecast:",
    ]

    for day in daily:
        lines.append(
            f"- {day['date']}: {day['condition']}, {day['high']}°F / {day['low']}°F, "
            f"{day['precipitation_chance']}% chance of precipitation"
        )

    return WeatherReport(
        park_code=park_code,
        park_name=park_name,
        prompt_text="\n".join(lines),
        current=current,
        daily=daily,
    )


async def get_weather(park_code: str) -> WeatherReport | None:
    async with httpx.AsyncClient() as client:
        data = await _fetch_weather(client, park_code)

    if not data:
        return None

    try:
        return _build_report(park_code, data)
    except (KeyError, IndexError, TypeError) as error:
        print(f"Weather parse error for {park_code}: {error}")
        return None


# fetches several parks at once over a shared connection pool; failures are skipped
async def get_weather_batch(park_codes: list[str]) -> list[WeatherReport]:
    if not park_codes:
        return []

    async with httpx.AsyncClient() as client:
        payloads = await asyncio.gather(
            *(_fetch_weather(client, park_code) for park_code in park_codes)
        )

    reports = []

    for park_code, data in zip(park_codes, payloads):
        if not data:
            continue

        try:
            reports.append(_build_report(park_code, data))
        except (KeyError, IndexError, TypeError) as error:
            print(f"Weather parse error for {park_code}: {error}")

    return reports



if __name__ == "__main__":
    test_parks = ["yose", "grca", "acad"]

    async def main():
        reports = await get_weather_batch(test_parks)

        for report in reports:
            print(f"\n{'=' * 60}")
            print(report.prompt_text)

        fetched = {report.park_code for report in reports}
        for park_code in test_parks:
            if park_code not in fetched:
                print(f"Failed to fetch weather for {park_code}")

    asyncio.run(main())
