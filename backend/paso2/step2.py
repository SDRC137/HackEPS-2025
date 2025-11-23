import pandas as pd
import json
import os
import sys
from dotenv import load_dotenv

# Add backend to path to import shared_constants
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared_constants import CATEGORY_SCALE

from backend.ranges_parser import (
    parse_ranges,
    determine_category,
    distance_score,
    category_spanish,
    category_index,
)

# Asegurar acceso a raíz del repo si se ejecuta este archivo directamente
ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_PATH not in sys.path:
    sys.path.append(ROOT_PATH)

# ==========================================
# AGENTE 2: MOTOR DE ANÁLISIS Y SCORING
# ==========================================

class Agent2Scorer:
    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path)
        ranges_path = os.path.join(os.path.dirname(__file__), "..", "ranges.md")
        self.ranges = parse_ranges(os.path.abspath(ranges_path))
        self.category_order = CATEGORY_SCALE
        # Direccionalidad (para futuras transformaciones específicas)
        self.directionality = {
            "crimes_per_100_people": "LOWER_BETTER",
            "median_rent": "LOWER_BETTER",
            "premium_stores_density": "LOWER_BETTER",
            "nightlife_density": "LOWER_BETTER",
            "local_businesses_density": "HIGHER_BETTER",
            "hospital_density": "HIGHER_BETTER",
        }

    def _sanitize_target(self, target_cat: str) -> str:
        # Ajustar variantes no estándar
        if target_cat == "Good/Moderate":
            return "Moderate"
        return target_cat if target_cat in self.category_order else "Moderate"

    def calculate_score(self, requirements_json: dict, excluded_neighborhoods: list = None):
        requirements = requirements_json.get("requirements", [])
        # Filtrar requisitos con peso válido (>0) y valor objetivo no nulo
        effective_requirements = []
        for r in requirements:
            weight = r.get("weight")
            value = r.get("value")
            var = r.get("variable_name")
            if not var:
                continue
            if weight is None or not isinstance(weight, (int, float)) or weight <= 0:
                continue
            if value is None:
                continue
            effective_requirements.append({
                "variable_name": var,
                "value": value,
                "weight": float(weight),
            })

        # Filtrar barrios excluidos antes de calcular
        df_to_score = self.df.copy()
        if excluded_neighborhoods:
            # Normalizar nombres para comparación insensible a mayúsculas/espacios
            excluded_norm = [n.lower().strip() for n in excluded_neighborhoods]
            df_to_score = df_to_score[~df_to_score["name"].str.lower().str.strip().isin(excluded_norm)]

        if not effective_requirements or df_to_score.empty:
            # Si no hay requisitos efectivos o barrios, devolver Top 3 por orden alfabético con score 0 (o vacío)
            if df_to_score.empty:
                return []
            
            base = df_to_score.sort_values("name").head(3)
            results = []
            for idx, row in base.iterrows():
                results.append({
                    "name": row["name"],
                    "total_score_raw": 0.0,
                    "total_score_pct": 0.0,
                    "coords": {"lat": 0, "lon": 0},
                    "details": {}
                })
            return results

        sum_weights = sum(r["weight"] for r in effective_requirements)

        # Cargar coordenadas si existen
        coords_map = {}
        pos_path = os.path.join(ROOT_PATH, "final_with_position.csv")
        if os.path.isfile(pos_path):
            try:
                temp_df = pd.read_csv(pos_path)
                for _, r in temp_df.iterrows():
                    coords_map[r["name"]] = {
                        "lat": r.get("latitude_centroid", 0),
                        "lon": r.get("longitude_centroid", 0),
                    }
            except Exception:
                pass

        score_accum = {idx: 0.0 for idx in df_to_score.index}
        explanation_data = {idx: {} for idx in df_to_score.index}

        for req in effective_requirements:
            col = req["variable_name"]
            target_cat = self._sanitize_target(req["value"])
            weight = req["weight"]
            if col not in df_to_score.columns:
                continue
            series = df_to_score[col]
            thresholds = self.ranges.get(col)

            for idx, val in series.items():
                # Determinar valor numérico si posible
                try:
                    numeric_val = float(val)
                except (TypeError, ValueError):
                    numeric_val = None

                if thresholds and numeric_val is not None:
                    actual_cat = determine_category(numeric_val, thresholds)
                else:
                    if isinstance(val, str) and val in self.category_order:
                        actual_cat = val
                    else:
                        actual_cat = "Moderate"

                pts = distance_score(actual_cat, target_cat, weight)
                score_accum[idx] += pts
                distance_ord = abs(category_index(actual_cat) - category_index(target_cat))
                explanation_data[idx][col] = {
                    "value": val,
                    "numeric_value": numeric_val,
                    "actual_category": actual_cat,
                    "actual_category_es": category_spanish(actual_cat),
                    "target_category": target_cat,
                    "target_category_es": category_spanish(target_cat),
                    "ordinal_distance": distance_ord,
                    "weight": weight,
                    "points_awarded": round(pts, 2),
                    "max_points": weight,
                    "thresholds": thresholds or {},
                }

        # Volcar acumulados al DataFrame
        df_to_score["final_score_raw"] = df_to_score.index.map(score_accum.get)
        df_to_score["final_score_pct"] = (df_to_score["final_score_raw"] / sum_weights * 100.0).round(2)
        top_3_df = df_to_score.sort_values(by="final_score_raw", ascending=False).head(3)
        results = []
        for idx, row in top_3_df.iterrows():
            name = row["name"]
            results.append(
                {
                    "name": name,
                    "total_score_raw": round(row["final_score_raw"], 2),
                    "total_score_pct": float(row["final_score_pct"]),
                    "coords": coords_map.get(name, {"lat": 0, "lon": 0}),
                    "details": explanation_data[idx],
                }
            )
        return results

# ==========================================
# AGENTE 3: RECOMENDACIÓN Y JUSTIFICACIÓN (LLM)
# ==========================================

 

# ==========================================
# EJECUCIÓN DEL FLUJO (MAIN)
# ==========================================

if __name__ == "__main__":
    # 0. Configuración: cargar .env y API KEY de Gemini
    load_dotenv()
    API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Input recibido del Agente 1 (El JSON de Jon Snow)
    input_json = {
        "client_name": "Jon Snow (El Guardià de la Comunitat)",
        "justification_summary": "Prioritza un barri pràctic, segur i de baix cost...",
        "requirements": [
            {"variable_name": "median_rent", "value": "Low", "weight": 5},
            {"variable_name": "premium_stores_density", "value": "Extremely_Low", "weight": 5},
            {"variable_name": "crimes_per_100_people", "value": "Low", "weight": 4},
            {"variable_name": "local_businesses_density", "value": "High", "weight": 4},
            {"variable_name": "air_quality_index", "value": "Good/Moderate", "weight": 3},
            {"variable_name": "hospital_density", "value": "Moderate", "weight": 3},
            {"variable_name": "nightlife_density", "value": "Low", "weight": 2}
        ]
    }

    print("--- INICIANDO AGENTE 2 (SCORING) ---")
    # Instanciar Agente 2
    try:
        scorer = Agent2Scorer(os.path.join(ROOT_PATH, "final.csv"))
        top_3_results = scorer.calculate_score(input_json)
        print(f"Top 1 Calculado: {top_3_results[0]['name']} (Score Raw: {top_3_results[0]['total_score_raw']}, %: {top_3_results[0]['total_score_pct']})")
        # print(json.dumps(top_3_results, indent=2)) # Descomentar para ver datos crudos
        
        print("\n--- INICIANDO AGENTE 3 (RECOMENDACIÓN) ---")
        # Instanciar Agente 3
        # Import tardío para evitar dependencia cuando solo se hace scoring
        from backend.paso3.step3 import Agent3Recommender
        recommender = Agent3Recommender(API_KEY)
        narrative, coords = recommender.generate_narrative(input_json, top_3_results)
        print("\n>>> RESPUESTA FINAL AL CLIENTE <<<\n")
        print(narrative)
        print(f"\n[Coordenadas para el Mapa: Lat {coords['lat']}, Lon {coords['lon']}]")

    except FileNotFoundError:
        print("Error: No se encuentra el archivo 'final.csv'. Por favor, cárgalo.")
    except Exception as e:
        print(f"Ocurrió un error: {e}")