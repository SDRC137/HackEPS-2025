# HackEPS 2025 – Intelligent Neighborhood Recommendation System (Los Angeles)
## By Porks in Paris

Project developed during the HackEPS 2025 hackathon. The goal is to help a user (potential relocation / move / investment) discover and compare Los Angeles neighborhoods in an explainable, iterative, and personalized way using a multi-agent pipeline and socio-demographic, housing, safety, and quality of life data.

## 🎥 Demo
[Watch the Demo Video](https://youtu.be/iVmeVIwP2Tk)

## 🧠 Main Idea
The system receives an initial profile (free text) and generates neighborhood recommendations with:
- Aggregated score and key factors (explainability).
- Top variables driving each recommendation.
- Map actions and nearby points of interest.
- Iterative cycle: the user can provide feedback and refine results (chat).

## ⚙️ Architecture
**Frontend (React + Vite + Tailwind + Radix + Mapbox GL)**
- Interactive interface: map, recommendation panel, chat-like feedback, visualizations.

**Backend (Flask + Agent Orchestrator)**
- REST Endpoint and CLI mode.
- Orchestrator (`BackendOrchestrator`) coordinates analysis, ranking, and text generation.
- External integrations: Google Custom Search / Unsplash for images, Mapbox for visualization.
- Session maintains: message history, discarded neighborhoods, latest recommendations.

**Data**
- `final.csv`, `final_with_position.csv`: aggregated metrics by neighborhood (scores and raw variables).
- `neighborhoods.csv`, `neighborhoods_geometry.csv`: catalogs and geometries for the map.
- Folder `demograficas_sociales_vivienda_costevida_seguridad_entorno/`: raw and processed sources.
- JSON Cache in `backend/cache/` to speed up intermediate agent queries.

## ✨ Key Features
- Explainable recommendations (factors + justifications).
- Conversational feedback cycle (`/api/chat`).
- Dynamic neighborhood image fetching (Google / Unsplash).
- CLI for debugging and quick demos (`run_agents.py`).
- Ready to extend to new datasets or cities.

## 📁 Structure (summary)
```
backend/               → Flask API + orchestrator + agents (WIP)
frontend/              → React Client (Vite) + Mapbox + UI components
data/                  → Base LA CSV
demograficas_sociales_.../ → Enriched datasets
SDR/                   → Preparation and analysis scripts (prototypes)
final.csv              → Consolidated main dataset
```

## 🔌 API Endpoints
| Method | Route | Description | Body Example |
|--------|------|-------------|--------------|
| POST | `/api/start` | Starts session with initial profile | `{ "prompt": "Looking for a safe neighborhood with good cultural offerings" }` |
| POST | `/api/chat` | Iterative feedback / refinement | `{ "message": "Prioritize park access and low crime" }` |
| GET  | `/api/images?neighborhood=Echo%20Park` | Neighborhood images | – |
| GET  | `/health` | Health check | – |

Typical response (summarized) from `/api/start` / `/api/chat`:
```json
{
	"recommendations": [
		{
			"name": "Echo Park",
			"total_score": 87.4,
			"overview": "Neighborhood with cultural mix and good outdoor life",
			"top_5_variables": [
				{"variable_name": "green_areas", "justification": "Outstanding access to green areas"}
			],
			"key_factors": [
				{"variable": "crime_rate", "neighborhood_value": 0.21, "match_score": 9, "max_score": 10}
			]
		}
	],
	"chatbot_text": "I recommend starting with Echo Park and Silver Lake...",
	"map_actions": [{"label": "Show recommended", "type": "layer"}],
	"process_log": ["Data normalization", "Score calculation", "Explanation generation"]
}
```

## 🛠️ Installation and Setup
### Requirements
- Python 3.11+ (recommended)
- Node.js 18+ (or Bun)
- Access to external API keys (optional for images): Google Custom Search / Unsplash.

### Backend
```pwsh
cd backend
python -m venv .venv
./.venv/Scripts/Activate.ps1
pip install -r ../requirements.txt
# Copy example .env and fill in keys
python server.py
```
Default server: `http://0.0.0.0:5001`

### Frontend
```pwsh
cd frontend
npm install       # or bun install
npm run dev       # or bun run dev
```
Interface: usually at `http://localhost:5173`

### CLI Mode (debug / demo)
```pwsh
python backend/run_agents.py
```

## 🌱 Environment Variables (`backend/.env` example)
```
GOOGLE_API_KEY=your_api_key
GOOGLE_CX=your_cx_id
GEMINI_API_KEY=optional_if_matches
UNSPLASH_ACCESS_KEY=your_unsplash_key
MAPBOX_TOKEN=your_mapbox_token
```
If image keys are missing: the `/api/images` endpoint will return an empty list and the frontend can show placeholders.

## 📊 Data and Quality
Data comes from multiple compilations (cost of living, housing, safety, social environment). Transformations and normalizations are applied (see some scripts in `SDR/` and intermediate files). This repository does not guarantee absolute accuracy: use for exploratory purposes in the hackathon.

## 🚀 Roadmap (Future Ideas)
- Add authentication and persistent sessions.
- Improve explanation engine (contrast with city averages).
- Multi-city support (parameterize datasets).
- Distributed caching and async jobs for heavy analysis.
- User variable weight adjustment panel.
- Unit tests and data integrity validation.

## ⚖️ License
Pending definition (default: internal hackathon use). Can be migrated to MIT if the team approves.
