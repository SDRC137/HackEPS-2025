import json
import os

try:
	import google.generativeai as genai
	_GENAI_AVAILABLE = True
except ImportError:
	_GENAI_AVAILABLE = False


class Agent3Recommender:
	def __init__(self, gemini_api_key: str | None = None, model: str = "gemini-2.0-flash", temperature: float = 0.7):
		api_key = gemini_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
		if not api_key:
			raise RuntimeError("GEMINI_API_KEY/GOOGLE_API_KEY no definido. Configúralo en .env o variables de entorno.")
		if not _GENAI_AVAILABLE:
			raise RuntimeError("Paquete 'google-generativeai' no instalado. Ejecuta: pip install --upgrade google-generativeai")
		os.environ["GEMINI_API_KEY"] = api_key
		os.environ["GOOGLE_API_KEY"] = api_key
		genai.configure(api_key=api_key)
		self.model_name = model
		self.temperature = temperature

	def generate_narrative(self, client_profile, top_neighborhoods):
		if not top_neighborhoods:
			return {"overview": "No hay barrios para recomendar.", "top_5_variables": []}, {"lat": 0, "lon": 0}
		top_1 = top_neighborhoods[0]
		data_context = json.dumps(top_neighborhoods, indent=2)

		prompt_text = f"""
Eres un consultor inmobiliario empático y claro.
Cliente: {client_profile.get('client_name', 'Cliente')}
Resumen de necesidades: {client_profile.get('justification_summary', 'N/A')}

Entre todos los barrios analizados, el mejor encaje es: {top_1['name']}.

Datos del Top 3 (JSON para tu referencia):
{data_context}

Tu tarea es generar una respuesta estructurada en JSON para el frontend.
Formato JSON esperado:
{{
  "overview": "Párrafo resumen de la recomendación (aprox 50-80 palabras). Empieza recomendando el barrio y explica por qué encaja con el perfil general.",
  "top_5_variables": [
    {{
      "variable_name": "Nombre de la variable (ej: Alquiler asequible)",
      "justification": "Descripción justificada (ej: El alquiler se encuentra en un nivel moderado, lo que lo hace más accesible para tu presupuesto estudiantil.)"
    }},
    ... (hasta 5 variables más importantes)
  ]
}}

Instrucciones para 'top_5_variables':
- Selecciona las 5 variables que más han influido en la decisión o que son más relevantes para el usuario.
- 'variable_name' debe ser legible (no snake_case).
- 'justification' debe ser personalizada al perfil del usuario.

Instrucciones para 'overview':
- Tono humano, empático y profesional.
- Menciona el barrio ganador.
- Resume por qué es la mejor opción.

IMPORTANTE: Devuelve SOLO el JSON válido, sin bloques de código markdown.
"""

		try:
			model = genai.GenerativeModel(self.model_name)
			response = model.generate_content(prompt_text)
			raw_text = getattr(response, "text", "") or str(response)
			
			# Clean markdown if present
			raw_text = raw_text.replace("```json", "").replace("```", "").strip()
			
			narrative_data = json.loads(raw_text)
		except Exception as e:
			narrative_data = {
				"overview": f"Error generando narrativa: {e}",
				"top_5_variables": []
			}

		return narrative_data, top_1.get("coords", {"lat": 0, "lon": 0})

 