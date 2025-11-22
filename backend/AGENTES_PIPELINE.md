# Pipeline de Agentes (Backend) - Sistema Interactivo

Resumen estructurado del flujo de procesamiento de perfiles, recomendación de barrios y negociación interactiva.

## Objetivo
Proveer un sistema de recomendación inmobiliaria conversacional que:
1. Entienda un perfil inicial en lenguaje natural.
2. Recomiende barrios basándose en datos objetivos (scoring).
3. Explique las decisiones de forma humana.
4. **Negocie** con el usuario aceptando feedback, ajustando criterios y descartando opciones rechazadas.
5. **Visualice** puntos de interés reales (POIs) relacionados con los requisitos.

## Componentes Principales

### Agente 1 – Extracción de Requisitos (Cold Start)
- **Archivo:** `backend/paso1/agent1.py`
- **Input:** Texto libre (`first_input.txt`).
- **Función:** Convierte texto en JSON estructurado `{ variable_name, value, weight }`.
- **Modelo:** Gemini 2.0 Flash.

### Agente 2 – Scoring (Motor de Decisión)
- **Archivo:** `backend/paso2/step2.py`
- **Input:** JSON de requisitos + Lista de barrios excluidos (`excluded_neighborhoods`).
- **Datos:** `final.csv` (métricas) y `final_with_position.csv` (geo).
- **Lógica:** Calcula distancia ordinal ponderada. Filtra barrios explícitamente rechazados antes del cálculo.
- **Salida:** Top 3 barrios.

### Agente 3 – Generación Narrativa (Explicabilidad)
- **Archivo:** `backend/paso3/step3.py`
- **Input:** Perfil cliente + Top 3 + Historial de feedback.
- **Función:** Genera explicación natural. El prompt ahora considera el contexto de iteraciones previas ("Entiendo que X no te gustó...").
- **Modelo:** Gemini 2.0 Flash.

### Agente 4 – Negociador (Feedback Loop)
- **Archivo:** `backend/paso4/agent4.py`
- **Input:** Requisitos actuales + Feedback del usuario (texto).
- **Función:**
    1. Analiza la intención (cambio de preferencia, nuevo requisito, rechazo de barrio).
    2. Actualiza el JSON de requisitos (modifica valores/pesos).
    3. Extrae barrios rechazados (`rejected_neighborhoods`).
    4. Genera mensaje "puente" empático.
- **Modelo:** Gemini 2.0 Flash.

### Heurística de POIs (Visualización)
- **Archivo:** `backend/posicionesmapa.py`
- **Input:** Barrio ganador + Requisitos activos.
- **Función:** Consulta OpenStreetMap (Overpass API) para encontrar coordenadas reales de servicios relevantes (parques, escuelas, etc.) según lo que el usuario pidió.

## Flujo de Ejecución (Orquestador)
El script `backend/run_agents.py` gestiona el bucle infinito:

1. **Inicialización:** Carga `.env` y datasets.
2. **Cold Start:** Ejecuta **Agente 1** con `first_input.txt`.
3. **Bucle Interactivo:**
    - **Guardado de Estado:** Crea snapshot JSON en `backend/output/client_state_iter_X.json`.
    - **Scoring (Agente 2):** Calcula Top 3 (excluyendo rechazados).
    - **Narrativa (Agente 3):** Muestra recomendación.
    - **POIs:** Busca y lista puntos de interés reales.
    - **Input Usuario:** Espera feedback por consola.
    - **Negociación (Agente 4):** Procesa feedback → actualiza requisitos y lista de excluidos.
    - *Repite el ciclo con los nuevos criterios.*

## Entradas y Artefactos
- **Entrada Inicial:** `backend/first_input.txt`
- **Persistencia:** `backend/output/` (historial de cambios del perfil JSON).
- **Datasets:** `final.csv`, `final_with_position.csv`.

## Manejo de Memoria y Rechazos
- **Memoria de Criterios:** El objeto `client_input` se muta en cada iteración con los ajustes del Agente 4.
- **Memoria de Rechazos:** Se mantiene una lista `excluded_neighborhoods` en memoria durante la sesión. Si el usuario dice "No me gusta X", X se añade a la lista y el Agente 2 no lo volverá a sugerir.
- **Contexto Narrativo:** El resumen del perfil se actualiza concatenando el feedback reciente para que el Agente 3 tenga contexto conversacional.

## Ejecución
```bash
python3 backend/run_agents.py
```
Para salir del bucle, escribir: `salir`, `exit` o `fin`.

## Requisitos Técnicos
- Python 3.10+
- `google-generativeai` (para Agentes 1, 3, 4)
- `pandas`, `python-dotenv`
- Conexión a Internet (para Gemini API y Overpass API)
- Variable de entorno `GEMINI_API_KEY`

---
Última actualización automática del documento: generado por asistente.
