"""
Travel Planner Agent — main orchestrator.

Uses IBM Granite (via watsonx.ai) to understand user intent and dispatch
the appropriate tools to build a comprehensive travel plan.
"""

from __future__ import annotations

import json
import os
from typing import Any
from datetime import date, timedelta

from dotenv import load_dotenv

from src.models.granite_client import GraniteClient
from src.tools.weather_tool import summarize_weather, get_weather
from src.tools.destination_tool import suggest_destinations
from src.tools.itinerary_tool import build_itinerary
from src.tools.transport_tool import recommend_transport
from src.tools.accommodation_tool import recommend_accommodation
from src.tools.local_guide_tool import get_local_guide

load_dotenv()

_INTENT_SYSTEM = """You are an intent classifier for a travel planning assistant.
Analyze the user's message and extract their intent and travel parameters.
Respond ONLY with a JSON object — no prose."""


class TravelPlannerAgent:
    """
    Main AI agent that orchestrates all travel planning capabilities.
    Powered by IBM Granite on IBM watsonx.ai (IBM Cloud Lite).
    """

    def __init__(self) -> None:
        self.granite = GraniteClient()
        self.conversation_history: list[dict[str, str]] = []
        self.user_profile: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Intent extraction
    # ------------------------------------------------------------------

    def _extract_intent(self, message: str) -> dict[str, Any]:
        """Use Granite to classify user intent and extract parameters."""
        today = date.today().isoformat()
        prompt = f"""Today's date: {today}

User message: "{message}"

Extract intent and parameters. Respond ONLY with this JSON structure:
{{
  "intent": "suggest_destinations | build_itinerary | get_weather | recommend_transport | recommend_accommodation | local_guide | full_plan | general_question",
  "destination": "city, country or null",
  "origin": "departure city or null",
  "duration_days": 7,
  "travel_date": "YYYY-MM-DD or null",
  "return_date": "YYYY-MM-DD or null",
  "budget_usd": null,
  "interests": [],
  "travel_style": "budget | mid-range | luxury | null",
  "group_type": "solo | couple | family | group | null",
  "other_params": {{}}
}}"""
        raw = self.granite.generate_structured(_INTENT_SYSTEM, prompt, max_tokens=400)
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(raw[start:end])
        except (json.JSONDecodeError, ValueError):
            pass
        return {"intent": "general_question"}

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

    def _handle_suggest_destinations(self, intent: dict[str, Any]) -> dict[str, Any]:
        prefs = {
            "interests": intent.get("interests") or ["culture", "sightseeing"],
            "budget_usd": intent.get("budget_usd") or 2000,
            "duration_days": intent.get("duration_days") or 7,
            "departure_from": intent.get("origin") or "unspecified",
            "travel_style": intent.get("travel_style") or "mid-range",
            "group_type": intent.get("group_type") or "solo",
        }
        return suggest_destinations(prefs, self.granite)

    def _handle_itinerary(self, intent: dict[str, Any]) -> dict[str, Any]:
        destination = intent.get("destination") or "Paris, France"
        days = intent.get("duration_days") or 7
        prefs = {
            "budget_level": intent.get("travel_style") or "mid-range",
            "interests": intent.get("interests") or ["culture", "food"],
            "group_type": intent.get("group_type") or "solo",
        }
        return build_itinerary(destination, days, prefs, self.granite)

    def _handle_weather(self, intent: dict[str, Any]) -> dict[str, Any]:
        city = intent.get("destination") or "London"
        days = min(intent.get("duration_days") or 5, 7)
        weather = get_weather(city, days)
        return {"weather_summary": summarize_weather(city, days), "raw": weather}

    def _handle_transport(self, intent: dict[str, Any]) -> dict[str, Any]:
        origin = intent.get("origin") or "New York"
        destination = intent.get("destination") or "London"
        travel_date = intent.get("travel_date") or (date.today() + timedelta(days=30)).isoformat()
        prefs = {
            "budget_usd": intent.get("budget_usd") or 800,
            "travelers": 1,
        }
        return recommend_transport(origin, destination, travel_date, prefs, self.granite)

    def _handle_accommodation(self, intent: dict[str, Any]) -> dict[str, Any]:
        destination = intent.get("destination") or "Paris"
        check_in = intent.get("travel_date") or (date.today() + timedelta(days=30)).isoformat()
        duration = intent.get("duration_days") or 7
        check_out_dt = date.fromisoformat(check_in) + timedelta(days=duration)
        check_out = check_out_dt.isoformat()
        budget_per_night = int((intent.get("budget_usd") or 700) / duration)
        prefs = {
            "budget_per_night_usd": budget_per_night,
            "guests": 1,
            "location_pref": "city center",
        }
        return recommend_accommodation(destination, check_in, check_out, prefs, self.granite)

    def _handle_local_guide(self, intent: dict[str, Any]) -> dict[str, Any]:
        dest_raw = intent.get("destination") or "Paris, France"
        parts = [p.strip() for p in dest_raw.split(",")]
        city = parts[0]
        country = parts[1] if len(parts) > 1 else parts[0]
        prefs = {
            "interests": intent.get("interests") or ["culture", "food"],
            "travel_style": intent.get("travel_style") or "mid-range",
        }
        return get_local_guide(city, country, prefs, self.granite)

    def _handle_full_plan(self, intent: dict[str, Any]) -> dict[str, Any]:
        """Build a complete travel plan: weather + itinerary + transport + accommodation + guide."""
        destination = intent.get("destination") or "Paris, France"
        origin = intent.get("origin") or "New York"
        days = intent.get("duration_days") or 7
        travel_date = intent.get("travel_date") or (date.today() + timedelta(days=30)).isoformat()

        dest_parts = [p.strip() for p in destination.split(",")]
        city = dest_parts[0]
        country = dest_parts[1] if len(dest_parts) > 1 else dest_parts[0]

        plan: dict[str, Any] = {"destination": destination, "duration_days": days}

        # Weather
        plan["weather"] = {"summary": summarize_weather(city, min(days, 7))}

        # Itinerary
        plan["itinerary"] = build_itinerary(
            destination, days,
            {"budget_level": intent.get("travel_style") or "mid-range",
             "interests": intent.get("interests") or ["culture", "food"],
             "group_type": intent.get("group_type") or "solo"},
            self.granite,
        )

        # Transport
        plan["transport"] = recommend_transport(
            origin, destination, travel_date,
            {"budget_usd": int((intent.get("budget_usd") or 2000) * 0.3)},
            self.granite,
        )

        # Accommodation
        check_in = travel_date
        check_out = (date.fromisoformat(check_in) + timedelta(days=days)).isoformat()
        plan["accommodation"] = recommend_accommodation(
            city, check_in, check_out,
            {"budget_per_night_usd": int((intent.get("budget_usd") or 2000) * 0.4 / days),
             "guests": 1},
            self.granite,
        )

        # Local guide
        plan["local_guide"] = get_local_guide(city, country, {
            "interests": intent.get("interests") or ["culture", "food"],
        }, self.granite)

        return plan

    def _handle_general(self, message: str) -> dict[str, Any]:
        """Answer a general travel question using Granite."""
        system = (
            "You are a knowledgeable travel assistant. "
            "Answer the user's travel question helpfully and concisely."
        )
        answer = self.granite.generate_structured(system, message, max_tokens=600)
        return {"answer": answer}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(self, user_message: str) -> dict[str, Any]:
        """
        Process a user message and return a structured travel planning response.
        This is the main entry point for the agent.
        """
        self.conversation_history.append({"role": "user", "content": user_message})

        intent = self._extract_intent(user_message)
        intent_type = intent.get("intent", "general_question")

        dispatch = {
            "suggest_destinations": self._handle_suggest_destinations,
            "build_itinerary": self._handle_itinerary,
            "get_weather": self._handle_weather,
            "recommend_transport": self._handle_transport,
            "recommend_accommodation": self._handle_accommodation,
            "local_guide": self._handle_local_guide,
            "full_plan": self._handle_full_plan,
        }

        if intent_type in dispatch:
            if intent_type == "full_plan":
                result = dispatch[intent_type](intent)
            else:
                result = dispatch[intent_type](intent)
        else:
            result = self._handle_general(user_message)

        result["intent_detected"] = intent_type
        result["extracted_params"] = intent

        self.conversation_history.append({
            "role": "assistant",
            "content": json.dumps(result, indent=2),
        })

        return result

    def reset(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
        self.user_profile = {}
