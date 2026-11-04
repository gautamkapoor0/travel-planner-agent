"""
Weather tool — fetches real-time weather using Open-Meteo (free, no API key needed).
Geocoding via OpenStreetMap Nominatim (free).
"""

from __future__ import annotations

import os
import requests
from typing import Any
from dotenv import load_dotenv

load_dotenv()

WEATHER_BASE = os.getenv("WEATHER_API_BASE_URL", "https://api.open-meteo.com/v1/forecast")
NOMINATIM_BASE = os.getenv("NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org")

WMO_CODES: dict[int, str] = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog", 51: "Light drizzle", 53: "Moderate drizzle",
    55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow", 80: "Slight showers",
    81: "Moderate showers", 82: "Violent showers", 95: "Thunderstorm",
    96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


def geocode(city: str) -> tuple[float, float] | None:
    """Return (latitude, longitude) for a city name, or None if not found."""
    try:
        resp = requests.get(
            f"{NOMINATIM_BASE}/search",
            params={"q": city, "format": "json", "limit": 1},
            headers={"User-Agent": "TravelPlannerAgent/1.0"},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception:
        pass
    return None


def get_weather(city: str, days: int = 7) -> dict[str, Any]:
    """
    Fetch weather forecast for a city.

    Returns a dict with:
      - city: str
      - lat/lon: float
      - current: dict (temp_c, feels_like, condition, wind_kmh, humidity)
      - forecast: list of daily dicts (date, max_c, min_c, condition, precip_mm)
    """
    coords = geocode(city)
    if coords is None:
        return {"error": f"Could not geocode city: {city}"}

    lat, lon = coords
    days = min(max(days, 1), 16)

    try:
        resp = requests.get(
            WEATHER_BASE,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,apparent_temperature,weathercode,windspeed_10m,relativehumidity_2m",
                "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum",
                "forecast_days": days,
                "timezone": "auto",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        return {"error": str(exc)}

    current_raw = data.get("current", {})
    current = {
        "temp_c": current_raw.get("temperature_2m"),
        "feels_like_c": current_raw.get("apparent_temperature"),
        "condition": WMO_CODES.get(current_raw.get("weathercode", -1), "Unknown"),
        "wind_kmh": current_raw.get("windspeed_10m"),
        "humidity_pct": current_raw.get("relativehumidity_2m"),
    }

    daily = data.get("daily", {})
    forecast = []
    for i, date in enumerate(daily.get("time", [])):
        forecast.append({
            "date": date,
            "max_c": daily["temperature_2m_max"][i],
            "min_c": daily["temperature_2m_min"][i],
            "condition": WMO_CODES.get(daily["weathercode"][i], "Unknown"),
            "precip_mm": daily["precipitation_sum"][i],
        })

    return {
        "city": city,
        "lat": lat,
        "lon": lon,
        "current": current,
        "forecast": forecast,
    }


def summarize_weather(city: str, days: int = 5) -> str:
    """Return a human-readable weather summary string."""
    w = get_weather(city, days)
    if "error" in w:
        return f"Weather unavailable for {city}: {w['error']}"

    c = w["current"]
    lines = [
        f"📍 {city} — Current: {c['temp_c']}°C, {c['condition']}",
        f"   Feels like {c['feels_like_c']}°C | Wind {c['wind_kmh']} km/h | Humidity {c['humidity_pct']}%",
        "",
        "📅 Forecast:",
    ]
    for day in w["forecast"][:days]:
        lines.append(
            f"  {day['date']}: {day['min_c']}°C – {day['max_c']}°C, "
            f"{day['condition']}, Precip {day['precip_mm']} mm"
        )
    return "\n".join(lines)
