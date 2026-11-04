"""
Transport recommendation tool — uses IBM Granite to suggest transport options
(flights, trains, buses, car rental) between origin and destination.
"""

from __future__ import annotations
import json
from typing import Any

from src.models.granite_client import GraniteClient

SYSTEM_PROMPT = """You are a transport and logistics expert for travelers.
Provide practical, accurate transport recommendations including all realistic options,
with estimated costs, travel times, pros/cons, and booking tips.
Always respond with valid JSON only — no prose outside the JSON block."""


def recommend_transport(
    origin: str,
    destination: str,
    travel_date: str,
    preferences: dict[str, Any],
    granite: GraniteClient | None = None,
) -> dict[str, Any]:
    """
    Recommend transport options from origin to destination.

    Args:
        origin: Departure city/country
        destination: Arrival city/country
        travel_date: Approximate date (e.g. "2025-03-15")
        preferences: dict with optional keys:
          - budget_usd: int  max transport budget
          - priority: "cheapest" | "fastest" | "comfortable" | "scenic"
          - travelers: int  number of travelers
          - luggage: "light" | "standard" | "heavy"
    """
    if granite is None:
        granite = GraniteClient()

    budget = preferences.get("budget_usd", 500)
    priority = preferences.get("priority", "balanced")
    travelers = preferences.get("travelers", 1)
    luggage = preferences.get("luggage", "standard")

    user_prompt = f"""Recommend transport options from {origin} to {destination}.

Travel details:
- Approximate date: {travel_date}
- Number of travelers: {travelers}
- Budget for transport: USD {budget} per person
- Priority: {priority}
- Luggage: {luggage}

Respond ONLY with a JSON object in this exact format:
{{
  "origin": "{origin}",
  "destination": "{destination}",
  "date": "{travel_date}",
  "options": [
    {{
      "mode": "Flight",
      "operator_examples": ["Airline 1", "Airline 2"],
      "estimated_cost_usd": 350,
      "duration": "3h 20m",
      "pros": ["Fast", "Direct routes available"],
      "cons": ["Expensive", "Airport transfers needed"],
      "booking_tips": "Book 6-8 weeks in advance for best prices",
      "recommended_for": "Travelers prioritizing speed",
      "rank": 1
    }}
  ],
  "recommended_option": "Flight",
  "local_transport_tips": "Tips for getting around once at the destination",
  "visa_reminder": "Check visa requirements for your nationality"
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
