"""
Itinerary builder tool — uses IBM Granite to create day-by-day travel plans
for a given destination, duration, and preferences.
"""

from __future__ import annotations
import json
from typing import Any

from src.models.granite_client import GraniteClient

SYSTEM_PROMPT = """You are an expert travel itinerary planner. Create detailed, realistic,
day-by-day itineraries that balance sightseeing, rest, local experiences, and travel logistics.
Consider opening hours, distances between attractions, and local customs.
Always respond with valid JSON only — no prose outside the JSON block."""


def build_itinerary(
    destination: str,
    duration_days: int,
    preferences: dict[str, Any],
    granite: GraniteClient | None = None,
) -> dict[str, Any]:
    """
    Build a detailed day-by-day itinerary.

    Args:
        destination: City/country to visit (e.g. "Paris, France")
        duration_days: Number of days (1–14)
        preferences: dict with optional keys:
          - budget_level: "budget" | "mid-range" | "luxury"
          - interests: list[str]
          - mobility: "high" | "moderate" | "low"
          - dietary: str  e.g. "vegetarian", "halal"
          - group_type: "solo" | "couple" | "family" | "group"
    """
    if granite is None:
        granite = GraniteClient()

    duration_days = min(max(duration_days, 1), 14)
    budget = preferences.get("budget_level", "mid-range")
    interests = ", ".join(preferences.get("interests", ["culture", "food", "sightseeing"]))
    mobility = preferences.get("mobility", "moderate")
    dietary = preferences.get("dietary", "no restrictions")
    group = preferences.get("group_type", "solo")

    user_prompt = f"""Create a detailed {duration_days}-day itinerary for {destination}.

Traveler profile:
- Budget level: {budget}
- Interests: {interests}
- Physical mobility: {mobility}
- Dietary preference: {dietary}
- Group type: {group}

Respond ONLY with a JSON object in this exact format:
{{
  "destination": "{destination}",
  "duration_days": {duration_days},
  "budget_level": "{budget}",
  "itinerary": [
    {{
      "day": 1,
      "theme": "Arrival & Old Town Exploration",
      "morning": {{
        "activity": "Activity name",
        "description": "Brief description",
        "duration_hours": 2,
        "cost_usd": 0,
        "tips": "Practical tip"
      }},
      "afternoon": {{
        "activity": "Activity name",
        "description": "Brief description",
        "duration_hours": 3,
        "cost_usd": 15,
        "tips": "Practical tip"
      }},
      "evening": {{
        "activity": "Dinner recommendation",
        "description": "Brief description",
        "duration_hours": 2,
        "cost_usd": 25,
        "tips": "Reservation tip"
      }},
      "accommodation": "Hotel/hostel type recommendation",
      "daily_budget_usd": 80,
      "transport_tip": "How to get around today"
    }}
  ],
  "total_estimated_cost_usd": 600,
  "packing_tips": ["tip 1", "tip 2"],
  "local_phrases": [{{"phrase": "Hello", "translation": "local language"}}]
}}"""

    raw = granite.generate_structured(SYSTEM_PROMPT, user_prompt, max_tokens=2048)

    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(raw[start:end])
    except (json.JSONDecodeError, ValueError):
        pass

    return {"raw_response": raw, "error": "Could not parse structured JSON from Granite"}
