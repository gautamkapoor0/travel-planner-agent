"""
Destination suggester tool — uses IBM Granite to recommend destinations
based on user preferences, budget, and travel style.
"""

from __future__ import annotations
import json
from typing import Any

from src.models.granite_client import GraniteClient

SYSTEM_PROMPT = """You are an expert travel consultant with deep knowledge of global destinations.
Your role is to recommend travel destinations that perfectly match the user's preferences,
budget, and constraints. Always respond with structured, actionable recommendations.
Format your response as valid JSON only — no prose outside the JSON block."""


def suggest_destinations(
    preferences: dict[str, Any],
    granite: GraniteClient | None = None,
) -> dict[str, Any]:
    """
    Suggest top travel destinations given user preferences.

    preferences keys (all optional):
      - interests: list[str]   e.g. ["beaches", "history", "food"]
      - budget_usd: int        total trip budget in USD
      - duration_days: int     trip length
      - departure_from: str    origin city/country
      - travel_style: str      e.g. "backpacker", "luxury", "family"
      - climate_pref: str      e.g. "warm", "cold", "tropical"
      - avoid_countries: list[str]
    """
    if granite is None:
        granite = GraniteClient()

    interests = ", ".join(preferences.get("interests", ["culture", "sightseeing"]))
    budget = preferences.get("budget_usd", 2000)
    duration = preferences.get("duration_days", 7)
    departure = preferences.get("departure_from", "unspecified")
    style = preferences.get("travel_style", "standard")
    climate = preferences.get("climate_pref", "any")
    avoid = ", ".join(preferences.get("avoid_countries", [])) or "none"

    user_prompt = f"""Suggest 5 travel destinations for a traveler with these preferences:
- Interests: {interests}
- Budget: USD {budget} total for {duration} days
- Departure from: {departure}
- Travel style: {style}
- Preferred climate: {climate}
- Countries to avoid: {avoid}

Respond ONLY with a JSON object in this exact format:
{{
  "destinations": [
    {{
      "rank": 1,
      "city": "City Name",
      "country": "Country Name",
      "why": "2-3 sentence explanation why this matches the traveler",
      "estimated_cost_usd": 1500,
      "best_months": ["December", "January"],
      "highlights": ["highlight 1", "highlight 2", "highlight 3"],
      "travel_style_fit": "excellent"
    }}
  ]
}}"""

    raw = granite.generate_structured(SYSTEM_PROMPT, user_prompt, max_tokens=1200)

    # Extract JSON from response
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(raw[start:end])
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: return raw text wrapped
    return {"raw_response": raw, "error": "Could not parse structured JSON from Granite"}
