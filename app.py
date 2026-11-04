"""
Flask REST API for the Travel Planner Agent.
Exposes endpoints for chat, weather, destinations, itinerary, transport, and accommodation.
"""

from __future__ import annotations

import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from src.agent.planner_agent import TravelPlannerAgent
from src.tools.weather_tool import summarize_weather, get_weather

load_dotenv()

app = Flask(__name__, static_folder="static")
CORS(app)

# One agent instance per server (holds conversation history)
_agent: TravelPlannerAgent | None = None


def get_agent() -> TravelPlannerAgent:
    global _agent
    if _agent is None:
        _agent = TravelPlannerAgent()
    return _agent


# ------------------------------------------------------------------ #
# Static UI
# ------------------------------------------------------------------ #

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


# ------------------------------------------------------------------ #
# Health check
# ------------------------------------------------------------------ #

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Travel Planner Agent", "model": "IBM Granite"})


# ------------------------------------------------------------------ #
# Chat endpoint — natural language interface to the agent
# ------------------------------------------------------------------ #

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    POST /api/chat
    Body: { "message": "I want to plan a 7-day trip to Japan with $3000 budget" }
    Returns: structured travel planning response
    """
    data = request.get_json(force=True, silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    try:
        agent = get_agent()
        result = agent.chat(message)
        return jsonify(result)
    except EnvironmentError as exc:
        return jsonify({"error": str(exc), "hint": "Check your .env file"}), 503
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/reset", methods=["POST"])
def reset_conversation():
    """Reset the agent's conversation history."""
    get_agent().reset()
    return jsonify({"status": "conversation reset"})


# ------------------------------------------------------------------ #
# Dedicated tool endpoints
# ------------------------------------------------------------------ #

@app.route("/api/weather", methods=["GET"])
def weather():
    """GET /api/weather?city=Tokyo&days=5"""
    city = request.args.get("city", "London")
    days = int(request.args.get("days", 5))
    return jsonify({
        "summary": summarize_weather(city, days),
        "data": get_weather(city, days),
    })


@app.route("/api/destinations", methods=["POST"])
def destinations():
    """
    POST /api/destinations
    Body: { "interests": ["beaches","food"], "budget_usd": 2000, "duration_days": 7, ... }
    """
    from src.tools.destination_tool import suggest_destinations
    prefs = request.get_json(force=True, silent=True) or {}
    try:
        return jsonify(suggest_destinations(prefs, get_agent().granite))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/itinerary", methods=["POST"])
def itinerary():
    """
    POST /api/itinerary
    Body: { "destination": "Paris, France", "duration_days": 5, "preferences": {...} }
    """
    from src.tools.itinerary_tool import build_itinerary
    body = request.get_json(force=True, silent=True) or {}
    destination = body.get("destination", "Paris, France")
    duration = int(body.get("duration_days", 5))
    prefs = body.get("preferences", {})
    try:
        return jsonify(build_itinerary(destination, duration, prefs, get_agent().granite))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/transport", methods=["POST"])
def transport():
    """
    POST /api/transport
    Body: { "origin": "NYC", "destination": "London", "travel_date": "2025-06-01", "preferences": {...} }
    """
    from src.tools.transport_tool import recommend_transport
    body = request.get_json(force=True, silent=True) or {}
    origin = body.get("origin", "New York")
    destination = body.get("destination", "London")
    travel_date = body.get("travel_date", "2025-06-01")
    prefs = body.get("preferences", {})
    try:
        return jsonify(recommend_transport(origin, destination, travel_date, prefs, get_agent().granite))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/accommodation", methods=["POST"])
def accommodation():
    """
    POST /api/accommodation
    Body: { "destination": "Kyoto", "check_in": "2025-06-01", "check_out": "2025-06-08", "preferences": {...} }
    """
    from src.tools.accommodation_tool import recommend_accommodation
    body = request.get_json(force=True, silent=True) or {}
    destination = body.get("destination", "Tokyo")
    check_in = body.get("check_in", "2025-06-01")
    check_out = body.get("check_out", "2025-06-08")
    prefs = body.get("preferences", {})
    try:
        return jsonify(recommend_accommodation(destination, check_in, check_out, prefs, get_agent().granite))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/guide", methods=["POST"])
def local_guide():
    """
    POST /api/guide
    Body: { "destination": "Tokyo", "country": "Japan", "preferences": {...} }
    """
    from src.tools.local_guide_tool import get_local_guide
    body = request.get_json(force=True, silent=True) or {}
    destination = body.get("destination", "Tokyo")
    country = body.get("country", "Japan")
    prefs = body.get("preferences", {})
    try:
        return jsonify(get_local_guide(destination, country, prefs, get_agent().granite))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ------------------------------------------------------------------ #
# Entry point
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", 5000))
    debug = os.getenv("APP_DEBUG", "true").lower() == "true"
    print(f"\n🌍 Travel Planner Agent API running on http://localhost:{port}")
    print(f"   Powered by IBM Granite on IBM watsonx.ai")
    print(f"   Web UI: http://localhost:{port}/\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
