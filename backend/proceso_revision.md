# Revisión del Proceso (Agente 2 y 3)

## Resumen
Se ha ejecutado el flujo de scoring y generación de recomendación para el cliente usando `final.csv` y el prompt del Agente 3. Durante la revisión se identifican diversos aspectos mejorables en datos, normalización, cálculo de puntuaciones, contexto y narrativa.

## Problemas Detectados
- **Coordenadas 0,0**: El dataset usado por el Agente 2 (`final.csv`) no incluye columnas de latitud/longitud. Se devolvía 0,0. Solución aplicada: cruza con `final_with_position.csv`.
- **Hardcode de número de barrios (114)**: El prompt fija "Has analizado datos de 114 barrios" en lugar de derivarlo dinámicamente de `len(df)`. Riesgo de inconsistencias si cambia el dataset.
- **Escala de scoring sin normalización final**: Se suman `weight * (1 - |X_norm - T|)` para cada variable. El resultado puede superar el total intuitivo esperado y no se presenta la fracción respecto a la suma de pesos. Falta claridad sobre máximo posible.
- **Normalización Min-Max dependiente del dataset**: Se usa Min-Max dinámico por columna. Esto hace que añadir/eliminar barrios cambie scores relativos. Rango recomendado (según `ranges.md`) debería ser percentiles predefinidos para robustez y estabilidad temporal.
- **No uso de `ranges.md`**: Los percentiles definidos (P10–P90) permiten categorizar mejor y asignar distancias ordinales más interpretables. Actualmente se ignora el archivo y se mapea textual → número con una tabla fija parcial.
- **Mapeo categórico simplista**: `target_map` asigna valores uniformes: Moderate=0.50, High=0.75, etc. No distingue variables donde "más alto" es negativo (crimen, ruido). No hay inversión de lógica por variable (comentado en `ranges.md`).
- **Valores impresos sin contexto comparativo**: Se muestran números brutos (ej. alquiler 1411$) sin rango (mínimo, máximo, percentil) ni categoría. Usuario percibe falta de contexto.
- **Unidades dudosas de crimen**: `crimes_per_100_people` muestra valores >500 (ej. 545.89 rango P90) que parecen más propios de per 1000 o per 100k. Etiqueta potencialmente engañosa.
- **Inconsistencia léxica en narrativa**: El modelo generó "Moderada/Pobre" aunque el dataset tiene "Moderate". Falta control estructurado sobre traducciones y glosas.
- **Prompt con error tipográfico**: "Erest" en lugar de "Eres".
- **Tratamiento de columnas constantes**: Si una columna fuera constante se asigna 0.5; esto puede distorsionar valoración (debería quizá quedar neutra o excluirse del score).
- **Direccionalidad no ajustada**: Fórmula simétrica penaliza desviaciones en ambas direcciones igual; para variables donde solo importa ser menor (crimen) o mayor (negocios locales) debería aplicarse una distancia dirigida (ej. max(0, T - X)).
- **Posible sobrepeso de variables con rangos comprimidos**: Min-Max en columnas estrechas otorga pequeñas diferencias proximidad que se traducen en puntos casi completos sin real diferenciación sustantiva.
- **Narrativa mezcla idioma y formato**: Menciona puntos como "4.89 de 5" para un criterio con peso 5 pero otros aparecen como "2.5 puntos de 4" sin explicación del cálculo subyacente.
- **Sin auditoría de datos faltantes**: Columnas vacías (ej. `average_housing_age` en primera fila) no se comentan en la explicación; se asignan valores que podrían quedar silenciosamente en 0.5.
- **Ausencia de ranking secundario**: No se listan brevemente métricas donde el barrio ganador no es top y los rivales sí destacan; se pierde credibilidad.

## Riesgos
- **Cambios dinámicos en dataset ⇒ ruptura de interpretabilidad**.
- **Sesgos por mapeo estático** para variables con preferencia inversa.
- **Narrativa con cifras aisladas** puede generar mala percepción y dudas sobre rigor.

## Recomendaciones de Mejora
1. **Adoptar `ranges.md` como fuente canónica**: Calcular distancia ordinal (categoría actual vs categoría objetivo) en lugar de min-max crudo.
2. **Normalizar por suma de pesos**: Presentar score % = (score / suma_pesos)*100.
3. **Incorporar contexto**: Para cada valor mostrar (valor, categoría, percentil, rango). Ej: `median_rent=1411$ (Low; P18; rango 1324–1518)`.
4. **Direccionalidad inteligente**: Definir para cada variable si se busca "menor es mejor", "mayor es mejor" o "ideal intervalo" y ajustar función de distancia.
5. **Validar unidades y etiquetas**: Confirmar significado de `crimes_per_100_people`; renombrar si procede.
6. **Separar traducción de datos**: Preprocesar vocabulario (Moderate→"Moderado") evitando que el modelo invente variantes.
7. **Controlar prompt dinámico**: Reemplazar número fijo de barrios por `{len(df)}`.
8. **Manejo explícito de missing**: Registrar columnas con NaN y excluirlas del cálculo o asignar penalización leve documentada.
9. **Añadir ranking comparativo**: Mostrar para cada variable clave el orden del barrio vs Top 3.
10. **Corregir tipografías y estilo**: "Eres"; evitar signos de exclamación excesivos.
11. **Capa de explicación matemática**: Exponer fórmula y distancia para 2 ejemplos en narrativa para transparencia.
12. **Configurable mapping por variable**: Tabla JSON de metas por variable con tipo (numeric|categorical|inverted) y función de scoring.
13. **Cache de coordenadas**: Cargar siempre de `final_with_position.csv` y fallar con warning si falta.

## Próximos Pasos Propuestos
- Refactor del motor de scoring usando `ranges.md` (parser + categorización).
- Implementar generador de contexto enriquecido (percentil + categoría) para pasar al LLM.
- Añadir tests unitarios sobre cálculo de puntos (edge cases: todos iguales, extremos, categorías invertidas).
- Internacionalización: diccionario de términos y unidades.
- Revisión de calidad del dato de crimen y ruido.

## Conclusión
El flujo actual funciona pero la explicación y metodología necesitan mayor transparencia y alineación con los rangos definidos para garantizar interpretabilidad y confianza del usuario final.

---

# Mejoras Concretas Paso 2 y Paso 3 (con nuevo JSON)

## Paso 2 (Scoring)
- Aceptar JSON con `null` en `weight` o `value`: ya implementado. Se ignoran requisitos sin peso válido (>0) o sin valor objetivo.
- Distancia por categorías usando `ranges.md`: ya implementado. Score porcentual respecto a suma de pesos válida.
- Detalles enriquecidos por variable: ya implementado (`details` por barrio) con categoría actual, objetivo, distancia ordinal, puntos y umbrales.
- Coordenadas integradas: ya implementado cruzando con `final_with_position.csv`.
- Futuro: direccionalidad avanzada (LOWER_BETTER/HIGHER_BETTER/INTERVAL) con funciones específicas por variable.

## Paso 3 (Narrativa)
- Evitar números inventados: la narrativa debe consumir exclusivamente `details` del scorer para citar valores, categorías y puntos; prohibir cálculos internos del LLM.
- Contexto comparativo Top 3: pasar una tabla/JSON con contribuciones por variable y distancia al objetivo. Indicar “qué variables empujaron el score”.
- Corrección semántica: no usar unidades dudosas (p.ej. crimen “por 100 personas”); revisar etiquetas y traducir categorías con diccionario canónico.
- Plantilla estructurada: encabezado (barrio ganador y % del score), ventajas (variables con mayor contribución), trade-offs (distancias >1), alternativas (por qué 2º y 3º quedaron cerca), resumen.

## Ejemplo de problema (Criminalidad)
Frase generada: “la tasa de criminalidad es de 1083.49 por cada 100 personas … 3.31 sobre 4”.
- Problemas: unidad errónea (“por 100 personas”), puntuación 3.31/4 no coincide con la métrica de scoring actual.
- Solución: que el LLM cite exactamente `details['crimes_per_100_people']`: `value`, `actual_category_es`, `points_awarded`, `max_points` y, si hay, umbrales de `ranges.md` (contexto: P10–P90).

## Próximo ajuste sugerido
- Exponer en `top_3_results` un resumen `contribuciones` por barrio: lista ordenada de variables por `points_awarded` y su % del total. Paso 3 usará esa lista en la narrativa.
