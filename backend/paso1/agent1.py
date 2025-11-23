import os
import json
import re
import sys
from typing import List, Dict, Any

# Add backend to path to import shared_constants
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared_constants import COLUMNS, CATEGORY_SCALE, AIR_QUALITY_VALUES

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

def call_gemini(text: str) -> Dict[str, Any]:
	"""Call Gemini 2.0 Flash to extract requirements. Returns dict with 'requirements' or {} if unavailable."""
	api_key = os.environ.get("GEMINI_API_KEY")
	if not api_key or not _GENAI_AVAILABLE:
		return {}
	genai.configure(api_key=api_key)
	model = genai.GenerativeModel("gemini-2.0-flash")
	instructions = (
		"Eres un agente de extracción estructurada. Devuelve SOLO un objeto JSON: {\\n"
		"  \"requirements\": [ {\"variable_name\":..., \"value\":..., \"weight\": (1-5)}, ... ],\\n"
		"  \"osm_requirements\": [ {\"search_term\": \"...\", \"osm_tag\": \"key=value\"}, ... ]\\n"
		"}\\n"
		"1. Requirements (Variables CSV): " + ", ".join(COLUMNS) + ". "
		"Categorías: " + ", ".join(CATEGORY_SCALE) + ". "
		"Si el texto NO respalda una variable, value=null. Weight debe ser entero 1-5.\\n"
		"IMPORTANTE SOBRE DISTANCIAS: 'proximity_to_sea' y 'dist_downtown_km' son distancias en KM. "
		"Por tanto: 'Low' significa 'Cerca' (pocos km) y 'High' significa 'Lejos' (muchos km). "
		"Si el usuario dice 'quiero estar cerca del mar', value='Low' o 'Extremely_Low'. "
		"Si el usuario dice 'odio el mar' o 'lejos del centro', value='High' o 'Extremely_High'.\\n"
		"2. OSM Requirements (Puntos de Interés Físicos): "
		"Si el usuario menciona lugares físicos ESPECÍFICOS que no están cubiertos por las variables genéricas (ej: 'quiero un skatepark', 'escuela montessori', 'tienda de cómics', 'helipuerto'), "
		"añádelos aquí. Genera la etiqueta OpenStreetMap (OSM) más probable para 'osm_tag' (ej: 'sport=skateboard', 'shop=comics'). "
		"Si pide cosas genéricas como 'parques' o 'restaurantes' que YA están en las variables CSV (green_space, restaurant_density), NO los añadas aquí, úsalos en 'requirements'. "
		"Solo añade cosas muy específicas o 'de nicho' que el cliente secreto podría pedir."
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
	"""
	Infers requirements from natural language text using Gemini.
	Returns a dictionary with 'requirements' and 'osm_requirements'.
	"""
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
