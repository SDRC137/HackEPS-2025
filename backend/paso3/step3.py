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
			return [], {"lat": 0, "lon": 0}
		
		# We want to generate narratives for all top neighborhoods (up to 3)
		neighborhoods_to_process = top_neighborhoods[:3]
		data_context = json.dumps(neighborhoods_to_process, indent=2)
		
		# Extract requirements list for explicit context
		# Filter only active requirements (weight > 0) to reduce noise for the LLM
		full_reqs = client_profile.get('requirements', [])
		active_reqs = [r for r in full_reqs if r.get('weight') and r.get('weight') > 0]
		
		# If no active reqs (unlikely), fallback to full list or empty
		reqs_to_show = active_reqs if active_reqs else full_reqs
		reqs_text = json.dumps(reqs_to_show, indent=2)

		prompt_text = f"""
Eres un consultor inmobiliario empático y claro.
Cliente: {client_profile.get('client_name', 'Cliente')}
Resumen de necesidades (Texto original + Feedback): {client_profile.get('justification_summary', 'N/A')}

LISTA COMPLETA DE REQUISITOS ACTIVOS (Ordenados por importancia):
{reqs_text}

Datos de los mejores barrios (JSON para tu referencia):
{data_context}

Tu tarea es generar una respuesta estructurada en JSON para el frontend, con detalles para CADA uno de los barrios proporcionados.
Formato JSON esperado (una lista de objetos):
[
  {{
    "neighborhood_name": "Nombre del barrio 1",
    "overview": "Párrafo resumen de la recomendación para este barrio (aprox 50-80 palabras). Explica por qué encaja con el perfil.",
    "top_5_variables": [
      {{
        "variable_name": "Nombre de la variable (ej: Alquiler asequible)",
        "original_variable_key": "Clave original del JSON (ej: median_rent)",
        "justification": "Descripción justificada (ej: El alquiler se encuentra en un nivel moderado...)"
      }},
      ... (hasta 5 variables más importantes)
    ]
  }},
  ... (repetir para los otros barrios)
]

Instrucciones para 'top_5_variables':
- DEBES seleccionar las 5 variables más relevantes de la 'LISTA COMPLETA DE REQUISITOS ACTIVOS'.
- NO te limites solo a lo mencionado en el último feedback. Si el usuario pidió "seguridad" al principio y tiene peso alto, DEBE aparecer.
- Prioriza las variables con mayor 'weight' (peso) y mejor puntuación en el barrio.
- 'variable_name' debe ser legible (no snake_case).
- 'original_variable_key' DEBE ser exactamente la clave que aparece en el JSON de datos (ej: 'walk_score', 'total_crimes').
- 'justification' debe ser personalizada al perfil del usuario.

Instrucciones para 'overview':
- Tono humano, empático y profesional.
- Resume por qué es una buena opción.
- USA NEGRILLAS (markdown **) para resaltar las palabras clave o conceptos más importantes (ej: **seguridad**, **parques**, **precio asequible**).

IMPORTANTE: Devuelve SOLO el JSON válido (una lista), sin bloques de código markdown.
"""

		try:
			model = genai.GenerativeModel(self.model_name)
			response = model.generate_content(prompt_text)
			raw_text = getattr(response, "text", "") or str(response)
			
			# Clean markdown if present
			raw_text = raw_text.replace("```json", "").replace("```", "").strip()
			
			narrative_list = json.loads(raw_text)
		except Exception as e:
			print(f"Error generando narrativa: {e}")
			narrative_list = []

		# Return the list of narratives and the coords of the first one (as default center)
		top_1_coords = neighborhoods_to_process[0].get("coords", {"lat": 0, "lon": 0})
		return narrative_list, top_1_coords

 