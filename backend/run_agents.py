import os
import sys
import json
from dotenv import load_dotenv

# Paths: this file lives inside `backend/`
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)

# Ensure both backend/ and repo root are importable
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from backend.paso2.step2 import Agent2Scorer
from backend.paso3.step3 import Agent3Recommender


def main():
    # Cargar .env desde la raíz del repo para asegurar GEMINI_API_KEY
    env_path = os.path.join(REPO_ROOT, ".env")
    if os.path.isfile(env_path):
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        load_dotenv(override=True)

    # Data paths
    csv_path = os.path.join(REPO_ROOT, "final.csv")
    # Usa el nuevo formato de JSON
    input_json_path = os.path.join(PROJECT_ROOT, "newclientinput.json")

    if not os.path.isfile(csv_path):
        print("Error: No se encuentra 'final.csv' en la raíz del proyecto.")
        return
    if not os.path.isfile(input_json_path):
        print("Error: No se encuentra 'backend/newclientinput.json'.")
        return

    # Load input
    with open(input_json_path, "r", encoding="utf-8") as f:
        client_input = json.load(f)

    print("--- INICIANDO AGENTE 2 (SCORING) ---")
    scorer = Agent2Scorer(csv_path)
    top_3_results = scorer.calculate_score(client_input)

    if not top_3_results:
        print("No se han podido calcular recomendaciones (Top 3 vacío).")
        return

    top_1 = top_3_results[0]
    # Soporte para ambas salidas (versión nueva y anterior)
    score_label = (
        f"Score Raw: {top_1.get('total_score_raw', 'n/a')}, %: {top_1.get('total_score_pct', 'n/a')}"
        if 'total_score_raw' in top_1 or 'total_score_pct' in top_1
        else f"Score: {top_1.get('total_score', 'n/a')}"
    )
    print(f"Top 1 Calculado: {top_1['name']} ({score_label})")

    print("\n--- INICIANDO AGENTE 3 (RECOMENDACIÓN - Gemini) ---")
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not gemini_key:
        print(f"Error: GEMINI_API_KEY/GOOGLE_API_KEY no definido. Busca .env en: {env_path}")
        return
    # Asegurar ambas variables para SDKs
    os.environ["GEMINI_API_KEY"] = gemini_key
    os.environ["GOOGLE_API_KEY"] = gemini_key
    recommender = Agent3Recommender(gemini_api_key=gemini_key, model="gemini-2.0-flash")

    # No es necesario enriquecer coordenadas aquí; el Paso 2 ya las incluye

    narrative, coords = recommender.generate_narrative(client_input, top_3_results)

    print("\n>>> RESPUESTA FINAL AL CLIENTE <<<\n")
    print(narrative)
    print(f"\n[Coordenadas para el Mapa: Lat {coords['lat']}, Lon {coords['lon']}]")


if __name__ == "__main__":
    main()
