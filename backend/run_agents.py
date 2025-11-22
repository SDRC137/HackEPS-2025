import os
import sys
import json
import time
from dotenv import load_dotenv

# Paths: this file lives inside `backend/`
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)

# Ensure both backend/ and repo root are importable
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from backend.paso1.agent1 import infer_requirements
from backend.paso2.step2 import Agent2Scorer
from backend.posicionesmapa import get_important_locations

def run_analysis(client_input, scorer, recommender_class, gemini_key, excluded_neighborhoods=None):
    """Ejecuta Agente 2 y Agente 3 y muestra resultados. Retorna los nombres del Top 3."""
    print("\n--- 🔄 ANALIZANDO BARRIOS (Agente 2) ---")
    top_3_results = scorer.calculate_score(client_input, excluded_neighborhoods=excluded_neighborhoods)

    if not top_3_results:
        print("⚠️  No se han encontrado recomendaciones (Top 3 vacío).")
        print("Posible causa: Todos los barrios han sido descartados o los filtros son demasiado estrictos.")
        return []

    top_1 = top_3_results[0]
    score_label = (
        f"Score Raw: {top_1.get('total_score_raw', 'n/a')}, %: {top_1.get('total_score_pct', 'n/a')}"
        if 'total_score_raw' in top_1 or 'total_score_pct' in top_1
        else f"Score: {top_1.get('total_score', 'n/a')}"
    )
    print(f"🏆 Top 1 Calculado: {top_1['name']} ({score_label})")

    print("\n--- ✍️  GENERANDO NARRATIVA (Agente 3) ---")
    if not recommender_class or not gemini_key:
        print("⚠️  Agente 3 no disponible (falta API Key o librería).")
    else:
        try:
            recommender = recommender_class(gemini_api_key=gemini_key, model="gemini-2.0-flash")
            narrative, coords = recommender.generate_narrative(client_input, top_3_results)
            print("\n>>> 💬 RESPUESTA FINAL AL CLIENTE <<<\n")
            print(narrative)
            print(f"\n📍 [Coordenadas: Lat {coords['lat']}, Lon {coords['lon']}]")
        except Exception as e:
            print(f"❌ Error en Agente 3: {e}")

    # --- Heurística de POIs (Nuevo) ---
    print("\n--- 🗺️  BUSCANDO PUNTOS DE INTERÉS RELEVANTES ---")
    try:
        # Optimización: Solo buscar POIs para los 3 requisitos con mayor peso
        reqs = client_input.get("requirements", [])
        sorted_reqs = sorted([r for r in reqs if r.get('weight')], key=lambda x: x['weight'], reverse=True)[:3]
        
        pois = get_important_locations(top_1['name'], sorted_reqs)
        if pois:
            for var_name, data in pois.items():
                print(f"\n🔹 {var_name} ({data['count']} encontrados):")
                for loc in data['locations']:
                    print(f"   - {loc['name']} ({loc['type']}): [{loc['lat']}, {loc['lon']}]")
        else:
            print("No se encontraron puntos de interés específicos para tus requisitos principales en este barrio.")
    except Exception as e:
        print(f"⚠️  Error buscando POIs: {e}")
    
    return [r['name'] for r in top_3_results]

def main():
    # 1. Configuración
    env_path = os.path.join(REPO_ROOT, ".env")
    if os.path.isfile(env_path):
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        load_dotenv(override=True)

    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
        os.environ["GOOGLE_API_KEY"] = gemini_key

    # Imports diferidos
    try:
        from backend.paso3.step3 import Agent3Recommender
    except ImportError:
        Agent3Recommender = None
    
    try:
        from backend.paso4.agent4 import Agent4Negotiator
    except ImportError:
        Agent4Negotiator = None

    # Data paths
    csv_path = os.path.join(REPO_ROOT, "final.csv")
    first_input_path = os.path.join(PROJECT_ROOT, "first_input.txt")
    input_json_path = os.path.join(PROJECT_ROOT, "newclientinput.json")

    if not os.path.isfile(csv_path):
        print("Error: No se encuentra 'final.csv'.")
        return

    # 2. Cold Start (Agente 1)
    print("\n=== 🚀 INICIANDO SISTEMA DE RECOMENDACIÓN ===")
    
    client_input = {}
    profile_text = ""
    excluded_neighborhoods = []

    if os.path.isfile(first_input_path):
        print("📄 Leyendo perfil inicial...")
        with open(first_input_path, "r", encoding="utf-8") as f:
            profile_text = f.read().strip()
        
        print("🧠 Agente 1: Extrayendo requisitos...")
        agent1_output = infer_requirements(profile_text)
        
        if agent1_output and agent1_output.get("requirements"):
            client_input = {
                "client_name": "Usuario",
                "justification_summary": profile_text[:400],
                "requirements": agent1_output["requirements"],
            }
        else:
            print("⚠️  Agente 1 no devolvió requisitos válidos. Usando fallback.")
    
    if not client_input and os.path.isfile(input_json_path):
        print("📂 Cargando JSON por defecto...")
        with open(input_json_path, "r", encoding="utf-8") as f:
            client_input = json.load(f)

    if not client_input:
        print("❌ Error: No hay input válido.")
        return

    # Inicializar Scorer (Agente 2) una sola vez
    scorer = Agent2Scorer(csv_path)

    # Crear directorio de salida si no existe
    output_dir = os.path.join(PROJECT_ROOT, "output")
    os.makedirs(output_dir, exist_ok=True)

    # 3. Bucle Principal (Orquestador)
    iteration = 0
    current_top_3_names = []

    while True:
        iteration += 1
        # Guardar estado actual del JSON del cliente
        timestamp = int(time.time())
        state_filename = f"client_state_iter_{iteration}_{timestamp}.json"
        state_path = os.path.join(output_dir, state_filename)
        try:
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(client_input, f, ensure_ascii=False, indent=2)
            # print(f"💾 Estado guardado en: {state_filename}") # Verbose off
        except Exception as e:
            print(f"⚠️  No se pudo guardar el estado: {e}")

        # Paso A: Visualización (Agente 2 + 3)
        current_top_3_names = run_analysis(client_input, scorer, Agent3Recommender, gemini_key, excluded_neighborhoods)

        if not current_top_3_names:
            print("\n⚠️  ¡Nos hemos quedado sin opciones!")
            print("¿Quieres reiniciar la lista de barrios descartados? (s/n)")
            resp = input(">> ").strip().lower()
            if resp == 's':
                excluded_neighborhoods = []
                print("🔄 Lista de descartes reiniciada.")
                continue
            else:
                print("👋 Terminando sesión.")
                break

        # Paso B: Espera Activa
        print("\n" + "="*50)
        try:
            user_feedback = input("👤 TU (Escribe 'salir' para terminar): ").strip()
        except EOFError:
            break
        
        if user_feedback.lower() in ["salir", "exit", "quit", "fin"]:
            print("👋 ¡Hasta luego!")
            break
        
        if not user_feedback:
            continue

        # Paso C: Intercepción (Agente 4)
        if not Agent4Negotiator or not gemini_key:
            print("⚠️  Agente 4 no disponible. No se puede procesar feedback.")
            continue

        print("\n🤖 Agente 4 (Negociador): Analizando tu feedback...")
        try:
            negotiator = Agent4Negotiator(api_key=gemini_key)
            # Pasamos los nombres de los barrios actuales para que entienda "no me gusta ninguno"
            result = negotiator.process_feedback(client_input, user_feedback, current_top_3_names)
            
            # Mensaje Puente (Inmediato)
            bridge_msg = result.get("bridge_message", "Entendido, ajustando búsqueda...")
            print(f"\n💬 Agente 4 dice: \"{bridge_msg}\"")
            
            # Actualizar estado (Invisible)
            new_reqs = result.get("requirements")
            new_rejected = result.get("rejected_neighborhoods", [])
            
            if new_reqs:
                client_input["requirements"] = new_reqs
                # Actualizar resumen para contexto de Agente 3
                client_input["justification_summary"] += f" | Feedback reciente: {user_feedback}"
                
                if new_rejected:
                    excluded_neighborhoods.extend(new_rejected)
                    print(f"🚫 Barrios descartados: {', '.join(new_rejected)}")
                
                print("⚙️  (Criterios actualizados internamente...)")
                time.sleep(1) # Pequeña pausa dramática
            else:
                print("⚠️  No se generaron cambios en los requisitos.")

        except Exception as e:
            print(f"❌ Error en Agente 4: {e}")

if __name__ == "__main__":
    main()
