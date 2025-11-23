import os
import json
import re
import sys
from typing import Dict, Any, List

# Add backend to path to import shared_constants
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared_constants import COLUMNS, CATEGORY_SCALE, AIR_QUALITY_VALUES

try:
    import google.generativeai as genai
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False

class Agent4Negotiator:
    def __init__(self, api_key: str | None = None, model: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY no definido.")
        if not _GENAI_AVAILABLE:
            raise RuntimeError("Paquete 'google-generativeai' no instalado.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model)

    def process_feedback(self, current_requirements: Dict[str, Any], user_feedback: str, current_top_3_names: List[str] = None) -> Dict[str, Any]:
        """
        Analyzes user feedback and current state to generate:
        1. An empathetic bridge message.
        2. An updated list of requirements (merging changes).
        3. An updated list of OSM requirements (for specific physical places).
        """
        
        reqs_json_str = json.dumps(current_requirements.get("requirements", []), indent=2)
        osm_reqs_json_str = json.dumps(current_requirements.get("osm_requirements", []), indent=2)
        top_3_str = ", ".join(current_top_3_names) if current_top_3_names else "Ninguno"
        
        prompt = f"""
Eres el Agente 4, un "Negociador Empático" en un sistema de recomendación inmobiliaria.
Tu objetivo es entender el feedback del usuario sobre una recomendación previa y determinar QUÉ CAMBIOS aplicar a los criterios actuales.

**Entradas:**
1. **Requisitos Actuales (JSON):**
{reqs_json_str}

2. **Requisitos OSM Actuales (Lugares Físicos Específicos):**
{osm_reqs_json_str}

3. **Barrios Recomendados Recientemente:**
{top_3_str}

4. **Feedback del Usuario:**
"{user_feedback}"

**Variables Disponibles (CSV):**
{", ".join(COLUMNS)}

**Escala de Valores:**
{", ".join(CATEGORY_SCALE)}
(Para air_quality_index: {", ".join(AIR_QUALITY_VALUES)})

**Instrucciones:**
1. **Análisis de Intención:** Identifica qué quiere cambiar el usuario.
   - **Quejas:** Si dice "es muy caro", busca `median_rent` o `median_home_price`, pon valor `Low` o `Extremely_Low` y peso 5. Si dice "muy ruidoso", `average_dB_level` -> `Low`.
   - **Distancias:** Recuerda que `proximity_to_sea` y `dist_downtown_km` son distancias. "Cerca" = `Low`, "Lejos" = `High`.
     - Si dice "más cerca", "muy cerca" o "primera línea", usa `Extremely_Low`.
     - Si dice "cerca" o "a poca distancia", usa `Low`.
     - Si dice "lejos" o "no me gusta", usa `High` o `Extremely_High`.
   - **Nuevos Requisitos (Variables CSV):** Si dice "quiero gimnasios", `gym_density` -> `High`.
   - **Nuevos Requisitos (Lugares Físicos/OSM):** Si pide algo ESPECÍFICO que NO está en las variables CSV (ej: "bibliotecas", "tienda de cómics", "parque para perros", "cancha de baloncesto"), añádelo como `osm_modification`. Genera el `osm_tag` adecuado (ej: `amenity=library`, `shop=comics`, `leisure=dog_park`).
   - **Descartes:** Si dice "no me importa X", pon valor y peso a `null` para eliminarlo.
   - **Rechazo de Barrios:**
     - Si dice "No me gusta X" (donde X es un barrio), añádelo a `rejected_neighborhoods`.
     - Si dice "No me gusta ninguno" o "Ninguno de estos", añade TODOS los barrios de la lista "Barrios Recomendados Recientemente" a `rejected_neighborhoods`.

2. **Generación de Mensaje Puente:** Redacta una respuesta corta (1-2 frases).
   - Estructura: Validación + Reflejo + Acción.
   - Tono: Empático y profesional.

**Salida Esperada (JSON Puro):**
Devuelve SOLO los cambios (`modifications`, `osm_modifications`) y el mensaje. NO devuelvas la lista completa de requisitos, yo me encargo de fusionarla.
{{
  "bridge_message": "Texto del mensaje puente...",
  "modifications": [
    {{ "variable_name": "...", "value": "...", "weight": ... }}, // Para añadir o modificar variables CSV
    {{ "variable_name": "...", "value": null, "weight": null }} // Para eliminar un requisito existente
  ],
  "osm_modifications": [
    {{ "search_term": "biblioteca", "osm_tag": "amenity=library" }}, // Para añadir lugares específicos
    {{ "search_term": "...", "osm_tag": null }} // Para eliminar un lugar específico (si aplica)
  ],
  "rejected_neighborhoods": ["NombreBarrio1", "NombreBarrio2"]
}}
"""
        try:
            response = self.model.generate_content(prompt)
            raw_text = getattr(response, "text", "") or str(response)
            
            # Limpieza básica para extraer JSON
            match = re.search(r"\{\s*\"bridge_message\".*\}", raw_text, re.DOTALL)
            if match:
                json_str = match.group(0)
                result_data = json.loads(json_str)
                
                # --- LOGIC TO MERGE REQUIREMENTS ---
                existing_reqs = current_requirements.get("requirements", [])
                modifications = result_data.get("modifications", [])
                
                # Convert existing to dict for easy update
                reqs_dict = {r["variable_name"]: r for r in existing_reqs}
                
                for mod in modifications:
                    var_name = mod.get("variable_name")
                    if not var_name: continue
                    
                    # If value/weight are null, delete
                    if mod.get("value") is None and mod.get("weight") is None:
                        if var_name in reqs_dict:
                            del reqs_dict[var_name]
                    else:
                        # Update or Add
                        reqs_dict[var_name] = {
                            "variable_name": var_name,
                            "value": mod.get("value"),
                            "weight": mod.get("weight")
                        }
                
                # Convert back to list
                final_reqs = list(reqs_dict.values())

                # --- LOGIC TO MERGE OSM REQUIREMENTS ---
                existing_osm_reqs = current_requirements.get("osm_requirements", []) or []
                osm_modifications = result_data.get("osm_modifications", [])
                
                # Convert existing to dict for easy update (key by search_term)
                osm_reqs_dict = {r["search_term"]: r for r in existing_osm_reqs}
                
                for mod in osm_modifications:
                    term = mod.get("search_term")
                    if not term: continue
                    
                    if mod.get("osm_tag") is None:
                        if term in osm_reqs_dict:
                            del osm_reqs_dict[term]
                    else:
                        osm_reqs_dict[term] = {
                            "search_term": term,
                            "osm_tag": mod.get("osm_tag")
                        }
                
                final_osm_reqs = list(osm_reqs_dict.values())
                
                return {
                    "bridge_message": result_data.get("bridge_message", ""),
                    "requirements": final_reqs,
                    "osm_requirements": final_osm_reqs,
                    "rejected_neighborhoods": result_data.get("rejected_neighborhoods", [])
                }
                
            else:
                # Fallback si no hay JSON válido
                print("Error: No se encontró JSON válido en la respuesta del Agente 4.")
                return {
                    "bridge_message": "Entendido. Voy a intentar ajustar la búsqueda con tus comentarios.",
                    "requirements": current_requirements.get("requirements", []),
                    "osm_requirements": current_requirements.get("osm_requirements", []),
                    "rejected_neighborhoods": []
                }
                
        except Exception as e:
            print(f"Error en Agente 4: {e}")
            return {
                "bridge_message": "He tenido un problema procesando tu solicitud, pero revisaré los criterios.",
                "requirements": current_requirements.get("requirements", []),
                "osm_requirements": current_requirements.get("osm_requirements", []),
                "rejected_neighborhoods": []
            }
