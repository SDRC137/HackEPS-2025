Esta es la descripción conceptual detallada del flujo. La clave aquí es transformar tu sistema de una "tubería" (entra dato -> sale dato) a un **Ciclo de Conversación con Memoria**.

Aquí tienes el diseño de la lógica para el **Orquestador** y el **Agente 4**, enfocados en la experiencia de usuario y la retención de contexto.

---

### 1. El Orquestador: "El Cerebro Central"

El Orquestador deja de ser un simple script secuencial y se convierte en una **Máquina de Estados**. Su responsabilidad es mantener "viva" la sesión del usuario y gestionar los tiempos de respuesta.

#### Flujo Lógico del Orquestador:

1.  **Inicio de Sesión (Cold Start):**
    * Recibe el primer input.
    * Llama al **Agente 1** para crear el "Perfil Base" (JSON).
    * Guarda este JSON en una variable de memoria llamada `estado_actual`.

2.  **El Bucle Principal (The Loop):**
    * **Paso A - Visualización:** Muestra los resultados actuales (Top 3 + Narrativa Agente 3).
    * **Paso B - Espera Activa:** Se queda esperando a que el usuario escriba.
    * **Paso C - Intercepción:** Cuando el usuario escribe, el Orquestador analiza:
        * ¿Es un comando de salida? (Salir/Fin) -> Termina.
        * ¿Es feedback? -> Activa el **Agente 4**.

3.  **Gestión de la Respuesta (La Clave de la Conversación):**
    * El Orquestador envía `estado_actual` + `feedback_usuario` al Agente 4.
    * **Lo importante:** El Agente 4 devuelve dos cosas separadas:
        1.  Un **Mensaje Puente** ("Perfecto, entiendo que quieres...").
        2.  El **Nuevo JSON** (invisible para el usuario).
    * El Orquestador imprime *inmediatamente* el **Mensaje Puente**. Esto le da feedback instantáneo al humano de que fue escuchado.
    * *Mientras el usuario lee esa frase*, el Orquestador ejecuta en segundo plano al **Agente 2** (Cálculo matemático) y al **Agente 3** (Narrativa final).

---

### 2. El Agente 4: "El Negociador Empático"

Este agente no busca barrios. Su único trabajo es entender **Diferencias (Deltas)** y **Emociones**.

#### Lógica Interna del Agente 4:

Este agente debe realizar tres tareas mentales simultáneas antes de responder:

**Tarea 1: Análisis de Intención (El "Qué")**
* Lee el texto del usuario y lo compara con el `estado_actual`.
* Detecta qué variable está en conflicto.
    * *Ejemplo:* Si el JSON tiene `price: High` y el usuario dice "es muy caro", el agente detecta la contradicción.
* Identifica nuevos requisitos que no existían antes (ej: "ah, y tengo perro").

**Tarea 2: Modificación Quirúrgica (El "Cómo")**
* Toma el JSON y modifica **solo** los campos afectados.
* **Ajuste de Pesos:** Si el usuario se queja de algo, ese atributo sube automáticamente su `weight` (peso) al máximo (5), porque se ha convertido en un "deal-breaker" (punto crítico).
* **Limpieza:** Si el usuario dice "olvida lo del gimnasio", el agente pone ese valor a `null` en el JSON.

**Tarea 3: Generación del "Mensaje Puente" (El "Por Qué")**
* Aquí es donde generas la frase que pediste.
* La lógica del prompt debe ser: *"Reconoce explícitamente lo que el usuario pidió cambiar y confirma que vas a buscar basándote en ese cambio específico"*.
* **Estructura del mensaje que debe generar:**
    1.  **Validación:** "Perfecto", "Entendido", "Tomo nota".
    2.  **Reflejo:** Repetir brevemente la petición para confirmar comprensión ("quieres priorizar el silencio sobre la ubicación").
    3.  **Acción:** "Ajustando la búsqueda con estos nuevos criterios..."

---

### 3. Ejemplo de la Experiencia Final (User Journey)

Así es como se siente este diseño en la práctica para el usuario (y los jueces de la Hackathon):

1.  **Sistema:** Muestra **Barrio A** (Muy céntrico, ruidoso).
2.  [cite_start]**Usuario:** "Me gusta la zona, pero soy como Bran Stark[cite: 21], necesito silencio absoluto para trabajar."
3.  **Orquestador:** Pasa esto al Agente 4.
4.  **Agente 4 (Proceso Interno):**
    * [cite_start]*Detecta:* Referencia a Bran Stark = Silencio[cite: 23].
    * *Acción:* Busca variable `noise_level` en el JSON. Cambia valor a `Low`. Sube `weight` a 5.
    * *Redacta:* "¡Entendido! Siendo un perfil analista como Bran, el silencio es innegociable. He eliminado las zonas de tráfico ruidoso para buscarte un refugio tranquilo con buena conectividad."
5.  **Sistema (Output Inmediato):** "¡Entendido! Siendo un perfil analista como Bran..."
6.  **Sistema (Output tras 2 segundos):** Muestra **Barrio B** (Residencial, silencioso) con la justificación generada por el Agente 3.

### Por qué esto gana puntos en el reto:

1.  [cite_start]**Justificación Sólida[cite: 9, 13]:** Al confirmar el cambio ("He eliminado las zonas de tráfico..."), estás justificando *antes* de mostrar el resultado. Creas confianza.
2.  [cite_start]**Manejo del Cliente Secreto[cite: 86, 89]:** Si el cliente secreto cambia de opinión radicalmente a mitad de la demo, esta arquitectura no se rompe; simplemente actualiza el estado y pivota con elegancia, demostrando robustez.
3.  [cite_start]**Personalidad[cite: 7, 16]:** El mensaje puente permite mantener el "roleplay" (hablar como un asesor de Juego de Tronos) sin ensuciar los datos técnicos del JSON.