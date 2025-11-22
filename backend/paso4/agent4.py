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
        Analiza el feedback del usuario y el estado actual para generar:
        1. Un mensaje puente empático.
        2. Una lista de requisitos actualizada.
        """
        
        reqs_json_str = json.dumps(current_requirements.get("requirements", []), indent=2)
        top_3_str = ", ".join(current_top_3_names) if current_top_3_names else "Ninguno"
        
        prompt = f"""
Eres el Agente 4, un "Negociador Empático" en un sistema de recomendación inmobiliaria.
Tu objetivo es entender el feedback del usuario sobre una recomendación previa y ajustar los criterios de búsqueda.

**Entradas:**
1. **Requisitos Actuales (JSON):**
{reqs_json_str}

2. **Barrios Recomendados Recientemente:**
{top_3_str}

3. **Feedback del Usuario:**
"{user_feedback}"

**Variables Disponibles:**
{", ".join(COLUMNS)}

**Escala de Valores:**
{", ".join(CATEGORY_SCALE)}
(Para air_quality_index: {", ".join(AIR_QUALITY_VALUES)})

**Instrucciones:**
1. **Análisis de Intención:** Identifica qué quiere cambiar el usuario.
   - **Quejas:** Si dice "es muy caro", busca `median_rent` o `median_home_price`, pon valor `Low` o `Extremely_Low` y peso 5. Si dice "muy ruidoso", `average_dB_level` -> `Low`.
   - **Nuevos Requisitos:** Si dice "quiero gimnasios", `gym_density` -> `High`.
   - **Descartes:** Si dice "no me importa X", pon valor y peso a `null`.
   - **Rechazo de Barrios:**
     - Si dice "No me gusta X" (donde X es un barrio), añádelo a `rejected_neighborhoods`.
     - Si dice "No me gusta ninguno" o "Ninguno de estos", añade TODOS los barrios de la lista "Barrios Recomendados Recientemente" a `rejected_neighborhoods`.
   - **Reset:** Si pide "empezar de cero" o "borrar todo", devuelve requisitos vacíos (o por defecto) y `rejected_neighborhoods` vacío (o con comando especial).

2. **Generación de Mensaje Puente:** Redacta una respuesta corta (1-2 frases).
   - Estructura: Validación + Reflejo + Acción.
   - Tono: Empático y profesional.

**Salida Esperada (JSON Puro):**
{{
  "bridge_message": "Texto del mensaje puente...",
  "requirements": [
    {{ "variable_name": "...", "value": "...", "weight": ... }},
    ... (lista completa actualizada)
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
                return json.loads(json_str)
            else:
                # Fallback si no hay JSON válido
                print("Error: No se encontró JSON válido en la respuesta del Agente 4.")
                return {
                    "bridge_message": "Entendido. Voy a intentar ajustar la búsqueda con tus comentarios.",
                    "requirements": current_requirements.get("requirements", []),
                    "rejected_neighborhoods": []
                }
                
        except Exception as e:
            print(f"Error en Agente 4: {e}")
            return {
                "bridge_message": "He tenido un problema procesando tu solicitud, pero revisaré los criterios.",
                "requirements": current_requirements.get("requirements", []),
                "rejected_neighborhoods": []
            }
