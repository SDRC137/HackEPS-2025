# HackEPS 2025 – Sistema Inteligente de Recomendación de Barrios (Los Ángeles)
## De Porks in Paris

Proyecto desarrollado durante el hackathon HackEPS 2025. El objetivo es ayudar a un usuario (potencial reubicación / mudanza / inversión) a descubrir y comparar barrios de Los Ángeles de forma explicable, iterativa y personalizada usando un pipeline multi‑agente y datos socio‑demográficos, vivienda, seguridad y calidad de vida.

## 🧠 Idea Principal
El sistema recibe un perfil inicial (texto libre) y genera recomendaciones de barrios con:
- Puntuación agregada y factores clave (explicabilidad).
- Top variables que motivan cada recomendación.
- Acciones de mapa y puntos de interés cercanos.
- Ciclo iterativo: el usuario puede dar feedback y refinar resultados (chat).

## ⚙️ Arquitectura
**Frontend (React + Vite + Tailwind + Radix + Mapbox GL)**
- Interfaz interactiva: mapa, panel de recomendaciones, feedback tipo chat, visualizaciones.

**Backend (Flask + Orquestador de Agentes)**
- Endpoint REST y modo CLI.
- Orchestrator (`BackendOrchestrator`) coordina análisis, ranking y generación de texto.
- Integraciones externas: Google Custom Search / Unsplash para imágenes, Mapbox para visualización.
- Sesión mantiene: historial de mensajes, barrios descartados, últimas recomendaciones.

**Datos**
- `final.csv`, `final_with_position.csv`: métricas agregadas por barrio (scores y variables crudas).
- `neighborhoods.csv`, `neighborhoods_geometry.csv`: catálogos y geometrías para mapa.
- Carpeta `demograficas_sociales_vivienda_costevida_seguridad_entorno/`: fuentes crudas y procesadas.
- Cache JSON en `backend/cache/` para acelerar consultas intermedias de agentes.

## ✨ Características Clave
- Recomendaciones explicables (factores + justificaciones).
- Ciclo de retroalimentación conversacional (`/api/chat`).
- Obtención dinámica de imágenes del barrio (Google / Unsplash).
- CLI para depuración y demostraciones rápidas (`run_agents.py`).
- Preparado para extender a nuevos conjuntos de datos o ciudades.

## 📁 Estructura (resumen)
```
backend/               → API Flask + orquestador + agentes (WIP)
frontend/              → Cliente React (Vite) + Mapbox + UI components
data/                  → CSV base LA
demograficas_sociales_.../ → Datasets enriquecidos
SDR/                   → Scripts de preparación y análisis (prototipos)
final.csv              → Dataset principal consolidado
```

## 🔌 Endpoints API
| Método | Ruta | Descripción | Body Ejemplo |
|--------|------|-------------|--------------|
| POST | `/api/start` | Inicia sesión con perfil inicial | `{ "prompt": "Busco barrio seguro con buena oferta cultural" }` |
| POST | `/api/chat` | Feedback iterativo / refinamiento | `{ "message": "Prioriza acceso a parques y baja criminalidad" }` |
| GET  | `/api/images?neighborhood=Echo%20Park` | Imágenes del barrio | – |
| GET  | `/health` | Comprobación de estado | – |

Respuesta típica (resumida) de `/api/start` / `/api/chat`:
```json
{
	"recommendations": [
		{
			"name": "Echo Park",
			"total_score": 87.4,
			"overview": "Barrio con mezcla cultural y buena vida al aire libre",
			"top_5_variables": [
				{"variable_name": "green_areas", "justification": "Acceso destacado a zonas verdes"}
			],
			"key_factors": [
				{"variable": "crime_rate", "neighborhood_value": 0.21, "match_score": 9, "max_score": 10}
			]
		}
	],
	"chatbot_text": "Te recomiendo empezar por Echo Park y Silver Lake...",
	"map_actions": [{"label": "Mostrar recomendados", "type": "layer"}],
	"process_log": ["Normalización datos", "Cálculo scores", "Generación explicación"]
}
```

## 🛠️ Instalación y Puesta en Marcha
### Requisitos
- Python 3.11+ (recomendado)
- Node.js 18+ (o Bun) 
- Acceso a claves API externas (opcional para imágenes): Google Custom Search / Unsplash.

### Backend
```pwsh
cd backend
python -m venv .venv
./.venv/Scripts/Activate.ps1
pip install -r ../requirements.txt
# Copiar .env de ejemplo y rellenar claves
python server.py
```
Servidor por defecto: `http://0.0.0.0:5001`

### Frontend
```pwsh
cd frontend
npm install       # o bun install
npm run dev       # o bun run dev
```
Interfaz: normalmente en `http://localhost:5173`

### Modo CLI (debug / demostración)
```pwsh
python backend/run_agents.py
```

## 🌱 Variables de Entorno (`backend/.env` ejemplo)
```
GOOGLE_API_KEY=tu_api_key
GOOGLE_CX=tu_cx_id
GEMINI_API_KEY=opcional_si_coincide
UNSPLASH_ACCESS_KEY=tu_unsplash_key
MAPBOX_TOKEN=tu_token_mapbox
```
Si faltan claves de imágenes: el endpoint `/api/images` devolverá lista vacía y el frontend puede mostrar placeholders.

## 📊 Datos y Calidad
Los datos provienen de compilaciones múltiples (coste de vida, vivienda, seguridad, entorno social). Se aplican transformaciones y normalizaciones (ver algunos de los scripts en `SDR/` y archivos intermedios). Este repositorio no garantiza exactitud absoluta: usar para fines exploratorios en el hackathon.

## 🚀 Roadmap (Ideas Futuras)
- Añadir autenticación y sesiones persistentes.
- Mejorar motor de explicación (contrastar con medias ciudad).
- Soporte multiciudad (parametrizar datasets).
- Cacheo distribuido y jobs asíncronos para análisis pesado.
- Panel de ajuste de pesos de variables por el usuario.
- Test unitarios y validación de integridad de datos.

## ⚖️ Licencia
Pendiente de definir (por defecto: uso interno hackathon). Se puede migrar a MIT si el equipo lo aprueba.
