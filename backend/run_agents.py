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

from backend.backend_api import BackendOrchestrator

def main():
    print("\n=== 🚀 INICIANDO SISTEMA DE RECOMENDACIÓN (CLI MODE) ===")
    
    orchestrator = BackendOrchestrator()
    
    # 1. Read Initial Input
    first_input_path = os.path.join(PROJECT_ROOT, "first_input.txt")
    profile_text = ""
    
    if os.path.isfile(first_input_path):
        print("📄 Leyendo perfil inicial...")
        with open(first_input_path, "r", encoding="utf-8") as f:
            profile_text = f.read().strip()
    else:
        profile_text = input("Escribe tu perfil aquí: ")

    if not profile_text:
        print("❌ Error: No hay texto de entrada.")
        return

    # 2. Start Session
    result = orchestrator.start_session(profile_text)
    
    while True:
        # Display Results
        if result["status"] == "empty":
            print("\n⚠️  ¡Nos hemos quedado sin opciones!")
            print("¿Quieres reiniciar la lista de barrios descartados? (s/n)")
            if input(">> ").strip().lower() == 's':
                orchestrator.session_state["excluded_neighborhoods"] = []
                result = orchestrator._run_analysis_cycle()
                continue
            else:
                break
        
        # --- NEW DISPLAY LOGIC FOR FRONTEND-FRIENDLY JSON ---
        print("\n>>> 💬 RESPUESTA FINAL AL CLIENTE (CHATBOT) <<<\n")
        print(result.get("overview", "No overview available."))
        
        print("\n--- 🔝 TOP 5 VARIABLES (JUSTIFICADAS) ---")
        for var in result.get("top_5_variables", []):
            print(f"   - {var['variable_name']}: {var['justification']}")

        print("\n--- 🗺️  ACCIONES DEL MAPA ---")
        for action in result.get("map_actions", []):
            print(f"   - {action['label']} ({action['type']})")
        
        print("\n--- 📊 DATOS ESTRUCTURADOS PARA EL FRONTEND ---")
        for i, rec in enumerate(result["recommendations"]):
            print(f"\n🏆 Opción {i+1}: {rec['name']} (Score: {rec['total_score']}%)")
            print("   Factores Clave (Explicabilidad):")
            for factor in rec["key_factors"]:
                print(f"   - {factor['variable']}: {factor['neighborhood_category']} (Valor: {factor['neighborhood_value']}) [Match: {factor['match_score']}/{factor['max_score']}]")

        # Show POIs including Custom ones
        pois = result.get("map_data", {}).get("pois", {})
        if pois:
            print("\n--- 🗺️  PUNTOS DE INTERÉS (MAPA) ---")
            for key, data in pois.items():
                label = data.get("label", key)
                print(f"\n🔹 {label} ({data['count']} encontrados):")
                for loc in data['locations']:
                    print(f"   - {loc['name']} ({loc['type']}): [{loc['lat']}, {loc['lon']}]")
        # ----------------------------------------------------

        # Feedback Loop
        print("\n" + "="*50)
        try:
            user_feedback = input("👤 TU (Escribe 'salir' para terminar): ").strip()
        except EOFError:
            break
            
        if user_feedback.lower() in ["salir", "exit", "quit", "fin"]:
            break
            
        if not user_feedback:
            continue
            
        # Process Feedback
        result = orchestrator.process_feedback(user_feedback)
        if "bridge_message" in result:
            print(f"\n💬 Agente 4 dice: \"{result['bridge_message']}\"")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
