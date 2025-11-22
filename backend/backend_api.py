import os
import json
import time
import sys
from dotenv import load_dotenv

# Ensure backend is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.paso1.agent1 import infer_requirements
from backend.paso2.step2 import Agent2Scorer
from backend.paso3.step3 import Agent3Recommender
from backend.paso4.agent4 import Agent4Negotiator
from backend.posicionesmapa import get_important_locations

class BackendOrchestrator:
    def __init__(self):
        self._load_env()
        self.scorer = self._init_scorer()
        self.recommender = self._init_recommender()
        self.negotiator = self._init_negotiator()
        self.geometry_map = self._init_geometry_loader()
        
        # Session state (could be moved to a database or Redis for a real web app)
        self.session_state = {
            "client_input": {},
            "excluded_neighborhoods": [],
            "current_top_3": [],
            "history": []
        }

    def _load_env(self):
        load_dotenv(override=True)
        self.gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.gemini_key:
            print("⚠️ Warning: GEMINI_API_KEY not found.")

    def _init_scorer(self):
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "final.csv")
        if os.path.exists(csv_path):
            return Agent2Scorer(csv_path)
        return None

    def _init_recommender(self):
        if self.gemini_key:
            return Agent3Recommender(gemini_api_key=self.gemini_key)
        return None

    def _init_negotiator(self):
        if self.gemini_key:
            return Agent4Negotiator(api_key=self.gemini_key)
        return None

    def _init_geometry_loader(self):
        """
        Loads neighborhood geometries from CSV into a dictionary.
        """
        geometry_map = {}
        try:
            import csv
            csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "neighborhoods_geometry.csv")
            if os.path.exists(csv_path):
                with open(csv_path, mode='r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        geometry_map[row['name']] = row['geometry']
            else:
                print(f"⚠️ Geometry CSV not found at {csv_path}")
        except Exception as e:
            print(f"⚠️ Error loading geometries: {e}")
        return geometry_map

    def start_session(self, user_text: str) -> dict:
        """
        Starts a new session with the initial user text.
        Returns a structured dictionary with results.
        """
        print(f"🚀 Starting session with text: {user_text[:50]}...")
        
        # Initialize history if not present
        if "history" not in self.session_state:
            self.session_state["history"] = []
            
        # Add user message to history
        self.session_state["history"].append({
            "role": "user",
            "content": user_text,
            "timestamp": int(time.time())
        })
        
        # 1. Agent 1: Extraction
        agent1_output = infer_requirements(user_text)
        
        self.session_state["client_input"] = {
            "client_name": "User",
            "justification_summary": user_text,
            "requirements": agent1_output.get("requirements", []),
            "osm_requirements": agent1_output.get("osm_requirements", []) # Capture custom needs
        }
        self.session_state["excluded_neighborhoods"] = []
        
        return self._run_analysis_cycle()

    def process_feedback(self, feedback_text: str) -> dict:
        """
        Processes user feedback on the current results.
        Returns updated results.
        """
        if not self.negotiator:
            return {"error": "Negotiator agent not available"}

        print(f"🔄 Processing feedback: {feedback_text}")
        
        # Add user feedback to history
        self.session_state["history"].append({
            "role": "user",
            "content": feedback_text,
            "timestamp": int(time.time())
        })
        
        # Agent 4: Negotiation
        current_top_names = [n['name'] for n in self.session_state["current_top_3"]]
        result = self.negotiator.process_feedback(
            self.session_state["client_input"], 
            feedback_text,
            current_top_names
        )
        
        # Update State
        if result.get("requirements"):
            self.session_state["client_input"]["requirements"] = result["requirements"]
        
        if result.get("rejected_neighborhoods"):
            self.session_state["excluded_neighborhoods"].extend(result["rejected_neighborhoods"])
            
        bridge_message = result.get("bridge_message", "Updating...")
        
        # Add agent response to history (bridge message)
        self.session_state["history"].append({
            "role": "assistant",
            "content": bridge_message,
            "timestamp": int(time.time())
        })
        
        # Re-run analysis
        analysis_result = self._run_analysis_cycle()
        analysis_result["bridge_message"] = bridge_message
        return analysis_result

    def _run_analysis_cycle(self) -> dict:
        """
        Internal method to run Scorer -> Recommender -> POI Search
        """
        if not self.scorer:
            return {"error": "Scorer not initialized (missing CSV?)"}

        # 2. Agent 2: Scoring
        top_3 = self.scorer.calculate_score(
            self.session_state["client_input"], 
            excluded_neighborhoods=self.session_state["excluded_neighborhoods"]
        )
        
        self.session_state["current_top_3"] = top_3
        
        # --- SAVE STATE TO DISK (Restored Feature) ---
        try:
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
            os.makedirs(output_dir, exist_ok=True)
            timestamp = int(time.time())
            state_filename = f"client_state_{timestamp}.json"
            state_path = os.path.join(output_dir, state_filename)
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(self.session_state["client_input"], f, ensure_ascii=False, indent=2)
            print(f"💾 Estado guardado en: {state_filename}")
        except Exception as e:
            print(f"⚠️  No se pudo guardar el estado: {e}")
        # ---------------------------------------------
        
        if not top_3:
            return {
                "status": "empty",
                "message": "No neighborhoods found matching criteria.",
                "top_3": []
            }

        # Select Top 2 for detailed response (or Top 3 if available)
        top_results = top_3[:3]
        
        # 3. Agent 3: Narrative (Generate for ALL Top results)
        narrative_list = []
        coords = {"lat": 0, "lon": 0}
        if self.recommender:
            narrative_list, coords = self.recommender.generate_narrative(
                self.session_state["client_input"], 
                top_results # Pass all top results
            )
            
        # Create a map of narratives by neighborhood name for easy lookup
        narrative_map = {item["neighborhood_name"]: item for item in narrative_list}

        # 4. POI Search (Map Data) for Top 1
        reqs = self.session_state["client_input"].get("requirements", [])
        custom_reqs = self.session_state["client_input"].get("osm_requirements", [])
        sorted_reqs = sorted([r for r in reqs if r.get('weight')], key=lambda x: x['weight'], reverse=True)[:3]
        
        # Construct Frontend-Friendly Response
        top_1_name = top_results[0]['name'] if top_results else "N/A"
        
        # Dynamic chatbot text based on history length or state
        if len(self.session_state.get("history", [])) <= 1:
             chatbot_text = f"He analizado tu perfil y el mejor barrio para ti es **{top_1_name}**. También he encontrado otras opciones interesantes."
        else:
             chatbot_text = f"He actualizado la búsqueda. **{top_1_name}** sigue siendo una gran opción, pero revisa cómo se ajusta a tus nuevos comentarios."

        process_log = [
            "Leyendo input...",
            "Computando posibilidades...",
            "Explicando justificación...",
            "Refinando selección..."
        ]

        response_data = {
            "status": "success",
            "chatbot_text": chatbot_text,
            "message_history": self.session_state.get("history", []),
            "process_log": process_log,
            "recommendations": []
        }

        for neighborhood in top_results:
            # Extract key factors (high weight & high score contribution)
            details = neighborhood.get("details", {})
            key_factors = []
            
            # Sort details by weight * points_awarded to find most impactful factors
            sorted_details = sorted(
                details.items(), 
                key=lambda item: item[1].get('weight', 0) * item[1].get('points_awarded', 0), 
                reverse=True
            )[:5] # Top 5 factors

            for var_name, info in sorted_details:
                key_factors.append({
                    "variable": var_name,
                    "user_weight": info.get("weight"),
                    "neighborhood_value": info.get("value"), # Raw value (e.g. "1200$")
                    "neighborhood_category": info.get("actual_category_es"), # e.g. "Bajo"
                    "match_score": info.get("points_awarded"), # How well it matched
                    "max_score": info.get("max_points")
                })
            
            # Get narrative data for this neighborhood
            n_data = narrative_map.get(neighborhood["name"], {})
            
            # --- Generate Map Actions & Data for this neighborhood ---
            # 1. POIs
            pois = get_important_locations(neighborhood['name'], sorted_reqs, custom_osm_requirements=custom_reqs)
            
            # 2. Distance Lines
            # Get centroid
            # Note: neighborhood dict from Scorer might not have centroid if not passed through. 
            # But we have geometry_map. We need centroid for lines.
            # Let's try to get it from the geometry string or just use a lookup if we had it.
            # Ideally Scorer should return it. Assuming Scorer returns 'coords' key as [lat, lon] or similar.
            # Checking Scorer output... it returns 'coords': {'lat': ..., 'lon': ...}
            
            center_lat = neighborhood.get('coords', {}).get('lat', 0)
            center_lon = neighborhood.get('coords', {}).get('lon', 0)
            
            map_actions = []
            
            # Distance to Downtown (Fixed Coords)
            downtown_coords = [34.0488, -118.2518]
            map_actions.append({
                "label": "Distancia a Downtown",
                "type": "line",
                "action": "show_line",
                "data": {
                    "start": [center_lon, center_lat], # GeoJSON uses [lon, lat]
                    "end": [downtown_coords[1], downtown_coords[0]],
                    "color": "#ff0000",
                    "label": "Downtown"
                }
            })
            
            # Distance to Sea (Santa Monica Pier as proxy)
            sea_coords = [34.0092, -118.4976]
            map_actions.append({
                "label": "Distancia a Playa",
                "type": "line",
                "action": "show_line",
                "data": {
                    "start": [center_lon, center_lat],
                    "end": [sea_coords[1], sea_coords[0]],
                    "color": "#0000ff",
                    "label": "Playa"
                }
            })
            
            # Add POI actions
            for key, data in pois.items():
                 label = data.get("label", key.replace("_", " ").title())
                 map_actions.append({
                     "label": label,
                     "type": "layer",
                     "data_key": key,
                     "count": data["count"],
                     "locations": data["locations"] # Pass locations directly
                 })

            response_data["recommendations"].append({
                "name": neighborhood["name"],
                "total_score": neighborhood["total_score_pct"],
                "coords": neighborhood["coords"],
                "overview": n_data.get("overview", "Sin descripción disponible."),
                "top_5_variables": n_data.get("top_5_variables", []),
                "key_factors": key_factors,
                "all_details": details,
                "map_polygon": self.geometry_map.get(neighborhood["name"], ""),
                "map_actions": map_actions,
                "map_pois": pois # Keep raw POI data if needed
            })

        # --- SAVE FRONTEND RESPONSE TO DISK ---
        try:
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, "frontend_response.json"), "w", encoding="utf-8") as f:
                json.dump(response_data, f, ensure_ascii=False, indent=2)
            print(f"💾 Respuesta frontend guardada en: frontend_response.json")
        except Exception as e:
            print(f"⚠️  No se pudo guardar la respuesta frontend: {e}")
        # --------------------------------------

        return response_data

# Simple test if run directly
if __name__ == "__main__":
    orch = BackendOrchestrator()
    res = orch.start_session("I want a quiet place with a skatepark and good vegan food.")
    print(json.dumps(res, indent=2, default=str))
