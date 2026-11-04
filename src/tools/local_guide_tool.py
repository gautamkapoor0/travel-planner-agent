"""
Local guide tool — uses IBM Granite to provide insider tips, must-try foods,
cultural etiquette, safety advice, and hidden gems for a destination.
Also fetches country info via REST Countries API.
"""

from __future__ import annotations
import json
import os
import requests
from typing import Any
from dotenv import load_dotenv

from src.models.granite_client import GraniteClient

load_dotenv()

REST_COUNTRIES_URL = os.getenv("REST_COUNTRIES_BASE_URL", "https://restcountries.com/v3.1")
EXCHANGE_RATE_URL = os.getenv("EXCHANGE_RATE_BASE_URL", "https://v6.exchangerate-api.com/v6")
EXCHANGE_RATE_KEY = os.getenv("EXCHANGE_RATE_API_KEY", "")

SYSTEM_PROMPT = """You are a local travel expert and cultural guide. Share insider knowledge,
authentic experiences, and practical safety tips that make a traveler's experience richer.
Highlight hidden gems beyond typical tourist traps.
Always respond with valid JSON only — no prose outside the JSON block."""


def get_country_info(country_name: str) -> dict[str, Any]:
    """Fetch basic country info from REST Countries API (free, no key)."""
    try:
        resp = requests.get(
            f"{REST_COUNTRIES_URL}/name/{country_name}",
            params={"fields": "name,capital,currencies,languages,flags,population,timezones,region"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data and isinstance(data, list):
            c = data[0]
            currencies = list(c.get("currencies", {}).keys())
            languages = list(c.get("languages", {}).values())
            return {
                "name": c.get("name", {}).get("common", country_name),
                "capital": c.get("capital", ["N/A"])[0] if c.get("capital") else "N/A",
                "currencies": currencies,
                "languages": languages,
                "population": c.get("population"),
                "region": c.get("region"),
                "timezones": c.get("timezones", []),
                "flag_emoji": c.get("flags", {}).get("alt", ""),
            }
    except Exception:
        pass
    return {}


def get_local_guide(
    destination: str,
    country: str,
    preferences: dict[str, Any],
    granite: GraniteClient | None = None,
) -> dict[str, Any]:
    """
    Generate a local travel guide for a destination.

    Args:
        destination: City name (e.g. "Tokyo")
        country: Country name (e.g. "Japan")
        preferences: dict with optional keys:
          - interests: list[str]
          - dietary: str
          - travel_style: str
    """
    if granite is None:
        granite = GraniteClient()

    # Fetch live country data
    country_info = get_country_info(country)

    interests = ", ".join(preferences.get("interests", ["culture", "food"]))
    dietary = preferences.get("dietary", "no restrictions")
    style = preferences.get("travel_style", "standard")

    user_prompt = f"""Create a comprehensive local guide for {destination}, {country}.

Traveler profile:
- Interests: {interests}
- Dietary preferences: {dietary}
- Travel style: {style}

Respond ONLY with a JSON object in this exact format:
{{
  "destination": "{destination}",
  "country": "{country}",
  "must_see": [
    {{
      "name": "Attraction name",
      "type": "Museum/Park/Temple/etc.",
      "description": "Why it's special",
      "entry_fee_usd": 10,
      "best_time": "Morning",
      "insider_tip": "Hidden tip"
    }}
  ],
  "must_eat": [
    {{
      "dish": "Dish name",
      "description": "What it is",
      "where_to_try": "Type of restaurant/market",
      "avg_cost_usd": 5,
      "dietary_note": "vegan-friendly / contains pork / etc."
    }}
  ],
  "hidden_gems": ["gem 1", "gem 2", "gem 3"],
  "cultural_etiquette": ["tip 1", "tip 2", "tip 3"],
  "safety_tips": ["tip 1", "tip 2"],
  "best_time_to_visit": "Month range and why",
  "local_transport": "How locals get around",
  "money_tips": "ATM, cash vs card, tipping culture",
  "emergency_numbers": {{"police": "local number", "ambulance": "local number"}}
}}"""

    raw = granite.generate_structured(SYSTEM_PROMPT, user_prompt, max_tokens=1400)

    result: dict[str, Any] = {}
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            result = json.loads(raw[start:end])
    except (json.JSONDecodeError, ValueError):
        result = {"raw_response": raw, "error": "Could not parse structured JSON from Granite"}

    if country_info:
        result["country_facts"] = country_info

    return result
