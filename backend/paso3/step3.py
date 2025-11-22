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
			return "No hay barrios para recomendar.", {"lat": 0, "lon": 0}
		top_1 = top_neighborhoods[0]
		data_context = json.dumps(top_neighborhoods, indent=2)

		prompt_text = f"""
Eres un consultor inmobiliario empático y claro.
Cliente: {client_profile.get('client_name', 'Cliente')}
Resumen de necesidades: {client_profile.get('justification_summary', 'N/A')}

Entre todos los barrios analizados, el mejor encaje es: {top_1['name']}.

Datos del Top 3 (JSON para tu referencia):
{data_context}

Cómo debes responder (en lenguaje natural y fácil de entender):
1) Empieza con la recomendación del barrio ganador en 1 frase.
2) Justifica con 3-5 ideas clave que ayuden a la persona a decidirse.
   - Usa descriptores humanos basados en categorías (bajo, moderado, alto), no hables de "x puntos de y".
   - Explica con frases como: "el alquiler está en un nivel bajo respecto a la ciudad", "la densidad de comercios locales es alta, favorece la vida de barrio", etc.
3) Trade-offs honestos: si alguna métrica no está en el nivel deseado, coméntalo con suavidad y contrapesa con otras fortalezas.
4) Cierra con una frase corta sobre por qué los otros dos barrios quedaron cerca y cuándo podrían ser buena alternativa.

IMPORTANTE: Revisa el "Resumen de necesidades". Si el cliente ha dado feedback negativo sobre recomendaciones anteriores (ej: "No me gusta X"), menciona explícitamente que has tenido en cuenta ese cambio.
Ejemplo: "Entiendo que X no te convenció por Y, así que he buscado opciones que prioricen Z..."

Evita mencionar puntuaciones técnicas o porcentajes del algoritmo. Prioriza una explicación humana, comparativa y comprensible.
"""

		try:
			model = genai.GenerativeModel(self.model_name)
			response = model.generate_content(prompt_text)
			narrative = getattr(response, "text", "") or str(response)
		except Exception as e:
			narrative = f"Error generando narrativa: {e}"

		return narrative, top_1.get("coords", {"lat": 0, "lon": 0})

 