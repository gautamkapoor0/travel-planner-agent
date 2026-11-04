"""
Tests for the Travel Planner Agent.
Run: pytest tests/ -v

Weather and geocoding tests use real free APIs (no key needed).
IBM Granite tests are skipped if credentials are not configured.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

# ------------------------------------------------------------------ #
# Weather tool tests (real free API)
# ------------------------------------------------------------------ #

def test_geocode_known_city():
    """Nominatim should geocode Paris correctly."""
    from src.tools.weather_tool import geocode
    result = geocode("Paris")
    assert result is not None
    lat, lon = result
    assert 48.0 < lat < 49.5, f"Unexpected Paris latitude: {lat}"
    assert 1.5 < lon < 3.5, f"Unexpected Paris longitude: {lon}"


def test_get_weather_returns_dict():
    """get_weather should return a dict with expected keys for a valid city."""
    from src.tools.weather_tool import get_weather
    result = get_weather("London", days=3)
    assert isinstance(result, dict)
    if "error" not in result:
        assert "city" in result
        assert "current" in result
        assert "forecast" in result
        assert len(result["forecast"]) == 3


def test_get_weather_invalid_city():
    """get_weather should return an error key for an unknown city."""
    from src.tools.weather_tool import get_weather
    result = get_weather("XYZNotARealCity12345", days=3)
    assert "error" in result


def test_summarize_weather_string():
    """summarize_weather should return a non-empty string for a valid city."""
    from src.tools.weather_tool import summarize_weather
    summary = summarize_weather("Tokyo", days=3)
    assert isinstance(summary, str)
    assert len(summary) > 10


# ------------------------------------------------------------------ #
# Country info test (real free API)
# ------------------------------------------------------------------ #

def test_get_country_info_japan():
    """REST Countries API should return Japan's capital as Tokyo."""
    from src.tools.local_guide_tool import get_country_info
    info = get_country_info("Japan")
    if info:  # Skip gracefully if API is unreachable
        assert "capital" in info
        assert "Tokyo" in info["capital"] or info["capital"] == "Tokyo"


# ------------------------------------------------------------------ #
# Granite client tests (mocked — no real API call)
# ------------------------------------------------------------------ #

class TestGraniteClientMocked:
    """Test GraniteClient with mocked IBM watsonx.ai credentials."""

    def setup_method(self):
        """Reset singleton before each test."""
        from src.models import granite_client as gc_module
        gc_module.GraniteClient._instance = None

    def test_raises_without_api_key(self):
        """Should raise EnvironmentError when API key is missing."""
        from src.models.granite_client import GraniteClient
        with patch.dict(os.environ, {"WATSONX_API_KEY": "", "WATSONX_PROJECT_ID": "proj123"}):
            with pytest.raises(EnvironmentError, match="WATSONX_API_KEY"):
                GraniteClient()

    def test_raises_without_project_id(self):
        """Should raise EnvironmentError when project ID is missing."""
        from src.models.granite_client import GraniteClient
        with patch.dict(os.environ, {"WATSONX_API_KEY": "key123", "WATSONX_PROJECT_ID": ""}):
            with pytest.raises(EnvironmentError, match="WATSONX_PROJECT_ID"):
                GraniteClient()


# ------------------------------------------------------------------ #
# Agent orchestration tests (mocked Granite)
# ------------------------------------------------------------------ #

class TestTravelPlannerAgentMocked:
    """Test the TravelPlannerAgent with a fully mocked GraniteClient."""

    @pytest.fixture
    def mock_granite(self):
        """Return a mock GraniteClient that returns minimal valid JSON."""
        mock = MagicMock()
        mock.generate_structured.return_value = '{"intent": "get_weather", "destination": "Paris", "duration_days": 3}'
        return mock

    def test_chat_weather_intent(self, mock_granite):
        """Agent should detect weather intent and call weather tool."""
        from src.agent.planner_agent import TravelPlannerAgent
        agent = TravelPlannerAgent.__new__(TravelPlannerAgent)
        agent.granite = mock_granite
        agent.conversation_history = []
        agent.user_profile = {}

        # Mock _extract_intent to return a known intent
        agent._extract_intent = lambda msg: {
            "intent": "get_weather",
            "destination": "Paris",
            "duration_days": 3,
        }

        result = agent.chat("What is the weather in Paris?")
        assert result.get("intent_detected") == "get_weather"
        assert "weather_summary" in result or "raw" in result

    def test_reset_clears_history(self, mock_granite):
        """reset() should clear conversation history."""
        from src.agent.planner_agent import TravelPlannerAgent
        agent = TravelPlannerAgent.__new__(TravelPlannerAgent)
        agent.granite = mock_granite
        agent.conversation_history = [{"role": "user", "content": "test"}]
        agent.user_profile = {"name": "Alice"}
        agent.reset()
        assert agent.conversation_history == []
        assert agent.user_profile == {}


# ------------------------------------------------------------------ #
# Flask API tests
# ------------------------------------------------------------------ #

class TestFlaskAPI:
    """Test Flask API endpoints with mocked agent."""

    @pytest.fixture
    def client(self):
        from app import app as flask_app
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as c:
            yield c

    def test_health_endpoint(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert "IBM Granite" in data["model"]

    def test_weather_endpoint(self, client):
        resp = client.get("/api/weather?city=Tokyo&days=3")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "summary" in data
        assert "data" in data

    def test_chat_requires_message(self, client):
        resp = client.post("/api/chat",
                           json={},
                           content_type="application/json")
        assert resp.status_code == 400
        assert "error" in resp.get_json()
