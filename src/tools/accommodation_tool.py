"""
Accommodation recommendation tool — uses IBM Granite to suggest hotels,
hostels, Airbnb, and other stay options based on budget and preferences.
"""

from __future__ import annotations
import json
from typing import Any

from src.models.granite_client import GraniteClient

SYSTEM_PROMPT = """You are an expert travel accommodation advisor with deep knowledge of
global hospitality options across all budget levels. Provide practical, specific
recommendations with real neighborhood context and booking strategies.
Always respond with valid JSON only — no prose outside the JSON block."""


def recommend_accommodation(
    destination: str,
    check_in: str,
    check_out: str,
    preferences: dict[str, Any],
    granite: GraniteClient | None = None,
) -> dict[str, Any]:
    """
    Recommend accommodation options for a destination.

    Args:
        destination: City/country (e.g. "Kyoto, Japan")
        check_in: Date string (e.g. "2025-03-15")
        check_out: Date string (e.g. "2025-03-22")
        preferences: dict with optional keys:
          - budget_per_night_usd: int
          - accommodation_type: "hotel" | "hostel" | "airbnb" | "resort" | "any"
          - amenities: list[str]  e.g. ["wifi", "breakfast", "pool"]
          - guests: int
          - location_pref: str  e.g. "city center", "near beach", "quiet area"
    """
    if granite is None:
        granite = GraniteClient()

    budget = preferences.get("budget_per_night_usd", 80)
    acc_type = preferences.get("accommodation_type", "any")
    amenities = ", ".join(preferences.get("amenities", ["wifi", "breakfast"]))
    guests = preferences.get("guests", 1)
    location = preferences.get("location_pref", "city center")

    user_prompt = f"""Recommend accommodation options in {destination}.

Stay details:
- Check-in: {check_in}
- Check-out: {check_out}
- Guests: {guests}
- Budget per night: USD {budget}
- Accommodation type preference: {acc_type}
- Desired amenities: {amenities}
- Location preference: {location}

Respond ONLY with a JSON object in this exact format:
{{
  "destination": "{destination}",
  "check_in": "{check_in}",
  "check_out": "{check_out}",
  "options": [
    {{
      "rank": 1,
      "name": "Example Hotel Name",
      "type": "Hotel",
      "neighborhood": "City Center",
      "estimated_price_per_night_usd": 75,
      "rating": "4.2/5",
      "amenities": ["WiFi", "Breakfast", "AC"],
      "pros": ["Central location", "Good value"],
      "cons": ["Street noise", "Small rooms"],
      "booking_platform": "Booking.com / Expedia",
      "tips": "Ask for a room above 3rd floor to avoid street noise"
    }}
  ],
  "neighborhood_guide": {{
    "best_for_budget": "Neighborhood name and why",
    "best_for_sightseeing": "Neighborhood name and why",
    "avoid": "Areas to avoid and why"
  }},
  "booking_advice": "General booking tips for this destination"
}}"""

    raw = granite.generate_structured(SYSTEM_PROMPT, user_prompt, max_tokens=1200)

    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(raw[start:end])
    except (json.JSONDecodeError, ValueError):
        pass

    return {"raw_response": raw, "error": "Could not parse structured JSON from Granite"}
