import os
import json
import re
from typing import List, Dict, Any

try:
	import google.generativeai as genai
	_GENAI_AVAILABLE = True
except ImportError:
	_GENAI_AVAILABLE = False

try:
	from dotenv import load_dotenv
	load_dotenv()  # Carga valores de .env en el entorno
except Exception:
	pass  # Si no existe dotenv, se ignora

CATEGORY_SCALE = ["Extremely_Low", "Low", "Moderate", "High", "Extremely_High"]

# Column names from final.csv header
COLUMNS = [
	"median_household_income","surface_area","population_density","average_age","families_with_children_percentage",
	"rent_vs_own_percentage","unemployment_rate","education_level_percentage","total_crimes","violent_ratio",
	"property_ratio","violent_vs_property_ratio","crime_trend_slope","crimes_per_100_people","median_rent",
	"median_home_price","average_housing_age","air_quality_index","average_dB_level","maximum_dB_level","gym_density",
	"culture_density","local_businesses_density","restaurant_density","premium_stores_density","nightlife_density",
	"hospital_density","dist_downtown_km","proximity_to_sea","green_space_percentage","charging_stations_number",
	"walk_score","transit_score","bike_score","accessibility_score"
]

# Possible categorical values for air_quality_index (observed in dataset)
AIR_QUALITY_VALUES = [
	"Good", "Moderate", "Moderate/Poor", "Good/Moderate"
]

def call_gemini(text: str) -> Dict[str, Any]:
	"""Call Gemini 2.0 Flash to extract requirements. Returns dict with 'requirements' or {} if unavailable."""
	api_key = os.environ.get("GEMINI_API_KEY")
	if not api_key or not _GENAI_AVAILABLE:
		return {}
	genai.configure(api_key=api_key)
	model = genai.GenerativeModel("gemini-2.0-flash")
	instructions = (
		"Eres un agente de extracción estructurada. Devuelve SOLO un objeto JSON: {\\n"
		"  \"requirements\": [ {\"variable_name\":..., \"value\":..., \"weight\":...}, ... ]\\n}\\n"
		"Variables (orden estricto): " + ", ".join(COLUMNS) + ". "
		"Categorías permitidas cuantitativas: " + ", ".join(CATEGORY_SCALE) + ". "
		"air_quality_index: " + ", ".join(AIR_QUALITY_VALUES) + " o null. "
		"Peso: entero 1-5 (importancia) o null si no hay evidencia. "
		"Regla estricta: si 'value' es null, entonces 'weight' DEBE ser null. Nunca asignes weight sin value. "
		"Si el texto NO respalda una preferencia -> value=null, weight=null. No inventes. "
		"No añadas comentarios ni texto fuera del JSON."
	)
	prompt = instructions + "\nPerfil:\n" + text + "\nJSON:"  # Sencillo, sin roles especiales
	try:
		response = model.generate_content(prompt)
	except Exception:
		return {}
	raw = ""
	if hasattr(response, "text") and response.text:
		raw = response.text
	elif getattr(response, "candidates", None):
		raw = "\n".join(
			[
				"".join(
					[p.text for p in cand.content.parts if getattr(p, 'text', None)]
				) for cand in response.candidates
			]
		)
	match = re.search(r"\{\s*\"requirements\"\s*:\s*\[.*?\]\s*\}", raw, re.DOTALL)
	if not match:
		return {}
	block = match.group(0)
	block = re.sub(r",\s*\]", "]", block)
	block = re.sub(r",\s*\}", "}", block)
	try:
		data = json.loads(block)
		present = {r.get("variable_name") for r in data.get("requirements", [])}
		for col in COLUMNS:
			if col not in present:
				data["requirements"].append({"variable_name": col, "value": None, "weight": None})
		ordered = []
		lookup = {r["variable_name"]: r for r in data["requirements"]}
		for col in COLUMNS:
			ordered.append(lookup.get(col, {"variable_name": col, "value": None, "weight": None}))
		data["requirements"] = ordered
		return data
	except Exception:
		return {}

def infer_requirements(text: str) -> Dict[str, Any]:
	g = call_gemini(text)
	if g.get("requirements"):
		return g
	return {"requirements": [{"variable_name": c, "value": None, "weight": None} for c in COLUMNS]}

def main():
	import argparse
	parser = argparse.ArgumentParser(description="Infer requirement categories y guarda JSON en archivo.")
	parser.add_argument("text", help="Perfil en lenguaje natural.")
	parser.add_argument("--output", "-o", help="Ruta de archivo de salida JSON", default="requirements_output.json")
	args = parser.parse_args()
	result = infer_requirements(args.text)
	data = json.dumps(result, ensure_ascii=False)
	with open(args.output, "w", encoding="utf-8") as f:
		f.write(data)
	# Mensaje mínimo a stderr para confirmar (sin contaminar salida JSON por stdout)
	import sys
	print(f"[guardado] {args.output}", file=sys.stderr)

if __name__ == "__main__":
	main()
