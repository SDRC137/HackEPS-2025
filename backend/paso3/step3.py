import json
import os
from langchain_google_genai import ChatGoogleGenerativeAI


class Agent3Recommender:
	def __init__(self, gemini_api_key: str | None = None, model: str = "gemini-2.0-flash"):
		api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
		if not api_key:
			raise RuntimeError("GEMINI_API_KEY no definido. Configúralo en .env o env.")
		# Asegurar variable esperada por SDKs de Google
		os.environ["GOOGLE_API_KEY"] = api_key
		# Pasar API key de manera explícita (compatibilidad con versiones)
		self.llm = ChatGoogleGenerativeAI(
			model=model,
			temperature=0.7,
			api_key=api_key,
			google_api_key=api_key,
		)

	def generate_narrative(self, client_profile, top_neighborhoods):
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

		Evita mencionar puntuaciones técnicas o porcentajes del algoritmo. Prioriza una explicación humana, comparativa y comprensible.
		"""

		ai_message = self.llm.invoke(prompt_text)
		narrative = getattr(ai_message, "content", str(ai_message))

		return narrative, top_1["coords"]

 