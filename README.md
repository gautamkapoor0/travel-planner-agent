# ✈️ Travel Planner Agent

An AI-powered travel planning assistant built on **IBM Granite** (via IBM watsonx.ai IBM Cloud Lite).

> Plan trips intelligently — destinations, itineraries, weather, transport, accommodation, and local guides — all from natural language.

---

## 🏗️ Architecture

```
travel-planner-agent/
├── src/
│   ├── models/
│   │   └── granite_client.py      # IBM Granite via watsonx.ai
│   ├── tools/
│   │   ├── weather_tool.py        # Open-Meteo + Nominatim (free)
│   │   ├── destination_tool.py    # AI destination suggester
│   │   ├── itinerary_tool.py      # Day-by-day itinerary builder
│   │   ├── transport_tool.py      # Transport recommendations
│   │   ├── accommodation_tool.py  # Hotel/hostel suggestions
│   │   └── local_guide_tool.py    # Insider tips + REST Countries API
│   └── agent/
│       └── planner_agent.py       # Main orchestrator (intent → tools)
├── static/
│   └── index.html                 # Web UI (dark theme)
├── app.py                         # Flask REST API
├── cli.py                         # Rich CLI interface
├── tests/
│   └── test_agent.py              # pytest test suite
├── .env                           # ← Configure your IBM keys here
└── requirements.txt
```

---

## ☁️ IBM Cloud Lite Setup

This project uses **IBM Cloud Lite** (free tier) services:

| Service | Purpose | Cost |
|---|---|---|
| **IBM watsonx.ai** | Hosts IBM Granite LLM | Free (Lite tier) |
| **IBM Granite 13B Instruct** | NLP: intent detection, planning, recommendations | Free on Lite |

### Step 1 — Create an IBM Cloud account
1. Go to [cloud.ibm.com](https://cloud.ibm.com) → **Create a free account**

### Step 2 — Provision watsonx.ai
1. In the IBM Cloud catalog, search for **"watsonx.ai"** and provision it (Lite plan is free)
2. Open watsonx.ai → Create a **Project**
3. Go to **Manage → General** → copy your **Project ID**

### Step 3 — Create an API key
1. Click your profile → **Manage → Access (IAM) → API Keys**
2. Create a new API key and copy it

### Step 4 — Update `.env`
```env
WATSONX_API_KEY=your_actual_api_key
WATSONX_PROJECT_ID=your_actual_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-13b-instruct-v2
```

---

## 🚀 Quick Start

### Install dependencies
```bash
pip install -r requirements.txt
```

### Option A — Web UI (recommended)
```bash
python app.py
```
Open [http://localhost:5000](http://localhost:5000) in your browser.

### Option B — CLI
```bash
python cli.py
```

---

## 💬 What You Can Ask

| Intent | Example |
|---|---|
| **Suggest destinations** | "Suggest a beach holiday destination for $2000 for 7 days" |
| **Full trip plan** | "Plan a 7-day trip to Japan from New York with $3000" |
| **Weather** | "What's the weather in Paris next week?" |
| **Itinerary** | "Create a 5-day itinerary for Barcelona" |
| **Transport** | "How do I get from London to Rome cheaply?" |
| **Accommodation** | "Find hotels in Kyoto for $80/night" |
| **Local guide** | "Give me insider tips for visiting Tokyo" |

---

## 🔌 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/chat` | Natural language chat interface |
| POST | `/api/reset` | Reset conversation history |
| GET | `/api/weather?city=Tokyo&days=5` | Weather forecast |
| POST | `/api/destinations` | Suggest destinations |
| POST | `/api/itinerary` | Build itinerary |
| POST | `/api/transport` | Transport options |
| POST | `/api/accommodation` | Accommodation options |
| POST | `/api/guide` | Local travel guide |

### Chat example
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Plan a 5-day trip to Bali from Mumbai for $1500"}'
```

### Weather example
```bash
curl "http://localhost:5000/api/weather?city=Paris&days=5"
```

---

## 🧪 Running Tests

```bash
pip install pytest
pytest tests/ -v
```

Tests cover:
- Weather/geocoding (uses real free APIs — no key needed)
- Country info fetching
- GraniteClient credential validation (mocked)
- Agent orchestration logic (mocked Granite)
- Flask API endpoints

---

## 🌐 Free External APIs Used

| API | Purpose | Key Required? |
|---|---|---|
| [Open-Meteo](https://open-meteo.com) | Weather forecasts | ❌ No |
| [Nominatim / OSM](https://nominatim.openstreetmap.org) | Geocoding (city → lat/lon) | ❌ No |
| [REST Countries](https://restcountries.com) | Country facts, currencies, languages | ❌ No |
| [Exchange Rate API](https://www.exchangerate-api.com) | Currency conversion (optional) | ✅ Free tier |

---

## 🛠️ Technology Stack

- **IBM Granite 13B Instruct** — Core LLM for intent, planning, recommendations
- **IBM watsonx.ai** — IBM Cloud Lite inference endpoint
- **Flask** — REST API server
- **Rich** — Beautiful CLI rendering
- **ibm-watsonx-ai** — Official IBM SDK
- **Open-Meteo** — Real-time weather
- **OpenStreetMap Nominatim** — Free geocoding
- **REST Countries** — Country metadata

---

## 📝 License

MIT — Free to use, modify, and distribute.
