import os
import json
import time
import sys
import math
from dotenv import load_dotenv

# Ensure backend is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.paso1.agent1 import infer_requirements
from backend.paso2.step2 import Agent2Scorer
from backend.paso3.step3 import Agent3Recommender
from backend.paso4.agent4 import Agent4Negotiator
from backend.posicionesmapa import get_important_locations
from backend.shared_constants import VARIABLE_METADATA

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
        """
        Loads environment variables from .env file.
        """
        load_dotenv(override=True)
        self.gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.gemini_key:
            print("Warning: GEMINI_API_KEY not found.")

    def _init_scorer(self):
        """
        Initializes the Scorer agent (Agent 2).
        """
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "final.csv")
        if os.path.exists(csv_path):
            return Agent2Scorer(csv_path)
        return None

    def _init_recommender(self):
        """
        Initializes the Recommender agent (Agent 3).
        """
        if self.gemini_key:
            return Agent3Recommender(gemini_api_key=self.gemini_key)
        return None

    def _init_negotiator(self):
        """
        Initializes the Negotiator agent (Agent 4).
        """
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
                print(f"Geometry CSV not found at {csv_path}")
        except Exception as e:
            print(f"Error loading geometries: {e}")
        return geometry_map

    def reset_session(self):
        """
        Resets the session state to initial values.
        """
        print("Resetting session state...")
        self.session_state = {
            "client_input": {},
            "excluded_neighborhoods": [],
            "current_top_3": [],
            "history": []
        }
        return {"status": "success", "message": "Session reset"}

    def start_session(self, user_text: str) -> dict:
        """
        Starts a new session with the initial user text.
        Returns a structured dictionary with results.
        """
        print(f"Starting session with text: {user_text[:50]}...")
        
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
        t0 = time.time()
        agent1_output = infer_requirements(user_text)
        print(f"Agent 1 (Extraction) took: {time.time() - t0:.2f}s")
        
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

        print(f"Processing feedback: {feedback_text}")
        
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
            
        if result.get("osm_requirements"):
            self.session_state["client_input"]["osm_requirements"] = result["osm_requirements"]
            
        # Update justification summary with feedback to keep Agent 3 informed
        current_summary = self.session_state["client_input"].get("justification_summary", "")
        self.session_state["client_input"]["justification_summary"] = f"{current_summary}. User Feedback: {feedback_text}"
        
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

    def _sanitize_details(self, details):
        """
        Recursively sanitize dictionary to remove NaN/Infinity values.
        """
        if isinstance(details, dict):
            return {k: self._sanitize_details(v) for k, v in details.items()}
        elif isinstance(details, list):
            return [self._sanitize_details(v) for v in details]
        elif isinstance(details, float):
            if math.isnan(details) or math.isinf(details):
                return None
        return details

    def _run_analysis_cycle(self) -> dict:
        """
        Internal method to run Scorer -> Recommender -> POI Search
        """
        if not self.scorer:
            return {"error": "Scorer not initialized (missing CSV?)"}

        # 2. Agent 2: Scoring
        t1 = time.time()
        top_3 = self.scorer.calculate_score(
            self.session_state["client_input"], 
            excluded_neighborhoods=self.session_state["excluded_neighborhoods"]
        )
        print(f"Agent 2 (Scoring) took: {time.time() - t1:.2f}s")
        
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
            print(f"Estado guardado en: {state_filename}")
        except Exception as e:
            print(f"No se pudo guardar el estado: {e}")
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
        
        # Run Agent 3 Synchronously to ensure stability (Gemini client might have issues in threads)
        if self.recommender:
            try:
                narrative_list, coords = self.recommender.generate_narrative(
                    self.session_state["client_input"], 
                    top_results
                )
            except Exception as e:
                print(f"Error in Agent 3: {e}")
        
        # Create a map of narratives by neighborhood name for easy lookup
        narrative_map = {item["neighborhood_name"]: item for item in narrative_list}

        # 4. POI Search (Map Data) - Parallelized
        reqs = self.session_state["client_input"].get("requirements", [])
        custom_reqs = self.session_state["client_input"].get("osm_requirements", [])
        sorted_reqs = sorted([r for r in reqs if r.get('weight')], key=lambda x: x['weight'], reverse=True)
        
        pois_map = {} # neighborhood_name -> pois_dict
        
        import concurrent.futures
        
        def fetch_pois_for_neighborhood(neighborhood):
            # Only fetch POIs for top 5 requirements + custom
            return neighborhood['name'], get_important_locations(neighborhood['name'], sorted_reqs[:5], custom_osm_requirements=custom_reqs)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_pois = {executor.submit(fetch_pois_for_neighborhood, n): n for n in top_results}
            
            for future in concurrent.futures.as_completed(future_pois):
                try:
                    name, pois = future.result()
                    pois_map[name] = pois
                except Exception as e:
                    print(f"Error fetching POIs for a neighborhood: {e}")

        # 5. Construct Frontend-Friendly Response
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
                # Sanitize value to avoid NaN in JSON
                raw_val = info.get("value")
                if isinstance(raw_val, float) and (math.isnan(raw_val) or math.isinf(raw_val)):
                    raw_val = None

                key_factors.append({
                    "variable": var_name,
                    "user_weight": info.get("weight"),
                    "neighborhood_value": raw_val, # Raw value (e.g. "1200$")
                    "neighborhood_category": info.get("actual_category_es"), # e.g. "Bajo"
                    "match_score": info.get("points_awarded"), # How well it matched
                    "max_score": info.get("max_points")
                })
            
            # Get narrative data for this neighborhood
            n_data = narrative_map.get(neighborhood["name"], {})
            overview_text = n_data.get("overview", "")
            
            # Fallback overview if missing
            if not overview_text:
                overview_text = f"**{neighborhood['name']}** es una excelente opción basada en tus criterios. Destaca por su puntuación general del {neighborhood['total_score_pct']}%. Revisa los detalles a continuación para ver cómo encaja con tus necesidades."

            # --- Generate Map Actions & Data for this neighborhood ---
            # 1. POIs - Retrieved from parallel execution
            pois = pois_map.get(neighborhood['name'], {})
            
            # 2. Distance Lines
            center_lat = neighborhood.get('coords', {}).get('lat', 0)
            center_lon = neighborhood.get('coords', {}).get('lon', 0)
            
            downtown_coords = [34.0488, -118.2518]
            sea_coords = [34.0092, -118.4976]
            
            map_lines = [
                {
                    "label": "Distancia a Downtown",
                    "start": [center_lon, center_lat],
                    "end": [downtown_coords[1], downtown_coords[0]],
                    "color": "#ff0000"
                },
                {
                    "label": "Distancia a Playa",
                    "start": [center_lon, center_lat],
                    "end": [sea_coords[1], sea_coords[0]],
                    "color": "#0000ff"
                }
            ]
            
            map_buttons = []
            # Add POI actions
            for key, data in pois.items():
                 label = data.get("label", key.replace("_", " ").title())
                 map_buttons.append({
                     "label": label,
                     "type": "poi_layer",
                     "data_key": key,
                     "count": data["count"],
                     "locations": data["locations"] # Pass locations directly
                 })

            # Enrich Top 5 Variables with Chart Data (Deterministic Approach)
            # Instead of relying on LLM to pick variables, we pick the ones that contributed most to the score.
            enriched_top_5 = []
            
            # 1. Add Custom OSM Requirements (Always show them if requested)
            # These are high priority because they come from specific user feedback
            for key, data in pois.items():
                if data.get("is_custom"):
                    term = data.get("label", key).replace("📍 ", "").replace(" (Especial)", "")
                    count = data.get("count", 0)
                    
                    # Determine status
                    if count > 0:
                        match_explanation = f"¡Encontrado! Hay {count} {term} cerca."
                        match_score = 5
                        category = "Presente"
                        justification = f"Has pedido específicamente '{term}' y hemos encontrado {count} opciones en la zona."
                    else:
                        match_explanation = f"No se han encontrado {term} en un radio cercano."
                        match_score = 0
                        category = "No encontrado"
                        justification = f"Has pedido '{term}', pero no hemos detectado ninguno en esta zona específica."

                    # Create chart data
                    chart_data = {
                        "user_weight": 5, # Assume high importance for custom requests
                        "neighborhood_value": count,
                        "neighborhood_category": category,
                        "match_score": match_score,
                        "max_score": 5,
                        "unit": "lugares",
                        "match_explanation": match_explanation
                    }
                    
                    var_item = {
                        "variable_name": term.title(),
                        "original_variable_key": key,
                        "justification": justification,
                        "chart_data": chart_data
                    }
                    enriched_top_5.append(var_item)

            # 2. Add Standard CSV Variables
            # Sort details by contribution (weight * points)
            # details is a dict: {var_name: {weight, points_awarded, ...}}
            sorted_vars = sorted(
                details.items(),
                key=lambda item: item[1].get('weight', 0) * item[1].get('points_awarded', 0),
                reverse=True
            )

            # --- DEDUPLICATION LOGIC ---
            # Group similar variables to avoid redundancy (e.g. 4 types of crime stats)
            # We will only show the highest-scoring variable from each group.
            VARIABLE_GROUPS = {
                "Safety": ["total_crimes", "violent_ratio", "property_ratio", "violent_vs_property_ratio", "crime_trend_slope", "crimes_per_100_people"],
                "Housing": ["median_rent", "median_home_price", "rent_vs_own_percentage"],
                "Noise": ["average_dB_level", "maximum_dB_level"],
                "Mobility": ["walk_score", "transit_score", "bike_score", "accessibility_score"]
            }
            
            seen_groups = set()
            final_vars_to_show = []
            
            # Reverse mapping for quick lookup
            var_to_group = {}
            for group, vars_in_group in VARIABLE_GROUPS.items():
                for v in vars_in_group:
                    var_to_group[v] = group

            for original_key, info in sorted_vars:
                # Check if this variable belongs to a group we've already shown
                group = var_to_group.get(original_key)
                if group:
                    if group in seen_groups:
                        continue # Skip this variable as we already have a representative for this group
                    seen_groups.add(group)
                
                final_vars_to_show.append((original_key, info))
                
                # Limit to 5 standard vars (in addition to custom ones)
                if len(final_vars_to_show) >= 5:
                    break

            for original_key, info in final_vars_to_show:
                # Format value to max 2 decimals if float
                raw_val = info.get("value")
                formatted_val = raw_val
                if isinstance(raw_val, (int, float)):
                    if isinstance(raw_val, float) and (math.isnan(raw_val) or math.isinf(raw_val)):
                            formatted_val = "N/A"
                    else:
                            formatted_val = f"{float(raw_val):.2f}".rstrip('0').rstrip('.')
                
                # Get metadata
                meta = VARIABLE_METADATA.get(original_key, {})
                unit = meta.get("unit", "")
                friendly_name = meta.get("label", original_key.replace("_", " ").title())
                
                # Generate match explanation
                score_pct = 0
                if info.get("max_points", 0) > 0:
                    score_pct = (info.get("points_awarded", 0) / info.get("max_points")) * 100
                    
                match_text = "Coincidencia baja"
                if score_pct > 80:
                    match_text = "¡Coincidencia perfecta!"
                elif score_pct > 50:
                    match_text = "Buena coincidencia"
                
                category = info.get("actual_category_es", "")
                if category:
                    match_text += f" - El barrio tiene un nivel {category} para esta variable."

                chart_data = {
                    "user_weight": info.get("weight", 0),
                    "neighborhood_value": formatted_val,
                    "neighborhood_category": info.get("actual_category_es"),
                    "match_score": info.get("points_awarded", 0),
                    "max_score": info.get("max_points", 100),
                    "unit": unit,
                    "match_explanation": match_text
                }
                
                # Construct the variable item similar to what LLM used to output
                var_item = {
                    "variable_name": friendly_name,
                    "original_variable_key": original_key,
                    "justification": f"Esta variable es clave para tu búsqueda ({info.get('weight', 0)}/5). {match_text}",
                    "chart_data": chart_data
                }
                enriched_top_5.append(var_item)
            
            # Sort by user weight (descending) - already sorted by contribution, but let's stick to weight for display
            enriched_top_5.sort(key=lambda x: x.get("chart_data", {}).get("user_weight", 0), reverse=True)
            
            # Limit to top 6 total (e.g. 1 custom + 5 standard) to avoid UI clutter
            enriched_top_5 = enriched_top_5[:6]

            response_data["recommendations"].append({
                "name": neighborhood["name"],
                "total_score": neighborhood["total_score_pct"],
                "coords": neighborhood["coords"],
                "overview": overview_text,
                "top_5_variables": enriched_top_5,
                "key_factors": key_factors,
                "all_details": self._sanitize_details(details),
                "map_context": {
                    "center": {"lat": center_lat, "lon": center_lon},
                    "polygon": self.geometry_map.get(neighborhood["name"], ""),
                    "buttons": map_buttons,
                    "lines": map_lines
                }
            })

        # --- SAVE FRONTEND RESPONSE TO DISK ---
        try:
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, "frontend_response.json"), "w", encoding="utf-8") as f:
                json.dump(response_data, f, ensure_ascii=False, indent=2)
            print(f"Respuesta frontend guardada en: frontend_response.json")
        except Exception as e:
            print(f"No se pudo guardar la respuesta frontend: {e}")
        # --------------------------------------

        return response_data

# Simple test if run directly
if __name__ == "__main__":
    orch = BackendOrchestrator()
    res = orch.start_session("I want a quiet place with a skatepark and good vegan food.")
    print(json.dumps(res, indent=2, default=str))
