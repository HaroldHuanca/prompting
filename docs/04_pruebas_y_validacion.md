# Documento 04: Pruebas, Validación y Verificación de Determinismo
## Plataforma de Investigación Experimental (Prompt Engineering Research Lab)

**Tesis:** *Técnicas de Estructuración de Prompts en la Calidad de Código Generado por el Modelo de Lenguaje de Gran Escala ChatGPT-4o*  
**Metodología:** Cascada Adaptada (Fase 4: Pruebas y Validación)  
**Versión:** 1.0.0  
**Fecha:** 2026-10-26  
**Autor:** Ingeniero de Software Principal  

---

## 1. Alcance de las Pruebas y Validación

La fase de validación asegura que la plataforma experimental cumple estrictamente con los estándares metodológicos de la investigación científica en Inteligencia Artificial y Calidad de Software:
1. **Verificación de Determinismo (Greedy Decoding T=0.0):** Comprobar que sucesivas inferencias con la misma semilla y prompt generen hashes SHA-256 idénticos o respuestas con estabilidad reproducible.
2. **Pruebas de Integración con la API de OpenAI:** Validar el manejo adecuado de timeouts, respuestas válidas del modelo `gpt-4o`, cálculo de latencia de red e inferencia, y extracción de bloques Markdown con `clean_code_block()`.
3. **Pruebas de Exactitud del Pipeline de Evaluación:** Validar que Pytest capture aserciones aprobadas y fallidas de manera aislada; que Radon compute con precisión el Maintainability Index (MI), Complejidad Ciclomática (CC) y SLOC; y que `timeit` / `tracemalloc` midan el tiempo y memoria pico sin interferir entre corridas.
4. **Verificación de Reglas de Integridad Científica:** Comprobar que en códigos con error de sintaxis o fallo funcional, las métricas no calculables se almacenen como `NULL` (con `estado_medicion` en `error` o `no_disponible`) y **nunca como 0**.

---

## 2. Protocolo de Verificación de Determinismo (T=0.0)

### 2.1 Hipótesis y Criterio de Aceptación
- **Premisa:** Con `temperature=0.0`, el modelo de lenguaje de gran escala selecciona siempre el token con mayor probabilidad condicional (Greedy Decoding).
- **Procedimiento:** Ejecutar $N=3$ réplicas consecutivas para el mismo problema algorítmico y la misma técnica de prompt.
- **Criterio de Determinismo:** El hash SHA-256 de las soluciones extraídas (`hash_codigo_sha256`) debe ser coincidente entre corridas sucesivas bajo condiciones estables de la API, garantizando que las variaciones observadas en la investigación respondan exclusivamente a la técnica de prompt y no a variabilidad estocástica del LLM.

### 2.2 Script Automatizado de Verificación
El backend incorpora un test de determinismo que:
1. Envía el mismo prompt 3 veces consecutivas con `temperature=0.0`.
2. Calcula `sha256(clean_code_block(response))`.
3. Valida la coincidencia y reporta los metadatos en `registro_evento`.

---

## 3. Matriz de Casos de Prueba del Sistema

| ID | Módulo Evaluado | Procedimiento de Prueba | Resultado Esperado | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **TC-01** | `OpenAIService` | Inferencia directa con `gpt-4o` y `temperature=0.0` | Retorno de texto en Markdown con latencia registrada en ms | Superado |
| **TC-02** | `CodeExtractor` | Extracción de código con delimitadores ` ```python `, ` ``` ` y texto conversacional previo/posterior | Código Python puro extraído, `ast.parse()` exitoso, hash SHA-256 de 64 caracteres | Superado |
| **TC-03** | `PytestEvaluator` | Ejecución de casos de prueba sobre función correcta (`Two Sum`) | $100\%$ pruebas aprobadas, inserción en `resultado_prueba` | Superado |
| **TC-04** | `PytestEvaluator` | Ejecución de casos de prueba sobre código con fallo lógico | Identificación de prueba fallida, captura de `AssertionError` y traceback sin caer el servidor | Superado |
| **TC-05** | `RadonEvaluator` | Análisis estático sobre funciones con bucles anidados y condiciones | Cálculo de MI ($0-100$), CC global y desglose por función en `complejidad_funcion` | Superado |
| **TC-06** | `BenchmarkProfiler` | Medición con `timeit` (3 warmup + 10 runs) y `tracemalloc` | Inserción de 13 registros en `benchmark_corrida`, cálculo de tiempos válidos y memoria pico en bytes | Superado |
| **TC-07** | Integridad BD | Registro de medición cuando falla el análisis de sintaxis | `medicion_metrica.valor_numerico` es `NULL`, `estado_medicion = 'error'` (no 0) | Superado |
| **TC-08** | Vistas SQL | Consulta de `vw_resumen_pruebas` y `vw_resumen_benchmark` | Agregados correctos en tiempo real, concordancia con registros crudos | Superado |
| **TC-09** | Export Service | Descarga de endpoints `/api/export/csv` y `/api/export/json` | Archivos generados con cabeceras correctas y codificación UTF-8 | Superado |
| **TC-10** | Frontend UI | Navegación entre las 3 interfaces (Ingesta, Ejecución, Resultados) | Carga reactiva de componentes, actualización visual en tiempo real | Superado |

---

## 4. Guía de Ejecución de Pruebas Automatizadas

Para ejecutar el conjunto completo de pruebas automatizadas del backend:
```bash
source .venv/bin/activate
pytest tests/ -v
```

Los resultados detallados de cada corrida experimental quedan auditados con marcas temporales UTC en la tabla `registro_evento` de la base de datos PostgreSQL.

## 5. Salvaguardas de integridad para corridas con el modelo

- Una falla de autenticación, cuota, red o respuesta incompleta de OpenAI no se reemplaza por la solución de referencia. Se registra como ejecución fallida y no se incorpora como resultado del modelo.
- Las solicitudes usan `temperature=0.0`, un límite explícito de tokens de salida y no reintentan automáticamente. Se persisten el modelo reportado, los parámetros, los tokens, el motivo de finalización, la versión de plantilla y el hash del prompt; la matriz CSV/JSON exporta los campos de auditoría.
- El contenido común de las cuatro técnicas (enunciado, interfaz, restricciones, ejemplos oficiales e instrucciones de salida) es idéntico. Few-shot agrega demostraciones; Chain-of-Thought solicita analizar paso a paso, pero mantener el análisis fuera de la respuesta final; Role Prompting asigna un rol especializado. La interfaz de clase/método se extrae de la solución de referencia y se incluye como especificación, no como código de respuesta.
- El código generado se ejecuta en un proceso `bubblewrap` sin acceso a la red ni al espacio de archivos del proyecto, con límites de recursos. Si el aislamiento no está disponible, la evaluación falla explícitamente en vez de ejecutar el código en el proceso del backend.
- Cada combinación protocolo/problema/técnica/número de repetición es inmutable: una repetición duplicada se rechaza con HTTP 409 y no reemplaza el registro anterior. Para reintentar o ampliar la muestra debe utilizarse un número de repetición nuevo, conservando el fallo original.

### Limitaciones de interpretación

Una corrida por combinación problema/técnica permite formar la matriz, pero no estimar variabilidad ni probar diferencias estadísticamente. Además, el perfil de tiempo/memoria usa el primer caso funcional, que puede ser pequeño y no representativo del tamaño máximo permitido. Por tanto, esos valores son mediciones de ese caso específico, no evidencia suficiente de complejidad asintótica ni de una ventaja de rendimiento entre técnicas. Para inferencia estadística se requieren réplicas; para estudiar rendimiento se requieren casos de benchmark grandes y equivalentes por problema.

## 6. Línea base de los 30 problemas LeetCode

Se ejecutó una corrida por cada combinación de 30 problemas y 4 técnicas: 120 inferencias reales con el modelo reportado `gpt-4o-2024-08-06`, temperatura 0.0 y sin reintentos. Las 120 ejecuciones están guardadas; cada una tiene un hash de prompt y una versión de modelo auditables. El costo estimado a partir del uso de tokens fue USD 0.5392; es una estimación con tarifas públicas, no un cargo confirmado por el proveedor.

| Técnica | Aserciones aprobadas / 77 | Aprobación de aserciones | Ejecuciones que aprobaron todas las pruebas |
| :--- | ---: | ---: | ---: |
| Zero-Shot | 55 | 71.4% | 16/30 (53.3%) |
| Few-Shot | 58 | 75.3% | 20/30 (66.7%) |
| Chain-of-Thought | 58 | 75.3% | 18/30 (60.0%) |
| Role Prompting | 56 | 72.7% | 17/30 (56.7%) |
| **Total** | **227/308** | **73.7%** | **71/120 (59.2%)** |

Por dificultad, aprobaron todas las pruebas 33/40 ejecuciones fáciles, 20/40 medias y 18/40 difíciles. Los intervalos Wilson del 95% para aprobación completa por técnica se solapan ampliamente: Zero-Shot 36.1–69.8%, Few-Shot 48.8–80.8%, Chain-of-Thought 42.3–75.4% y Role Prompting 39.2–72.6%. Por tanto, la ventaja descriptiva de Few-Shot no demuestra que esa técnica sea superior.

El benchmark registró 1,200 mediciones (10 por ejecución) sobre el primer caso funcional. De ellas, 840 aprobaron la aserción de ese caso y 360 no; 84/120 ejecuciones tuvieron al menos una medición válida y 36 no tuvieron ninguna. Se guardaron además 360 corridas de calentamiento. Estos datos no evalúan tamaños de entrada grandes ni complejidad asintótica, así que los tiempos y memoria de esta corrida no deben usarse para afirmar una ventaja de rendimiento. La batería funcional contiene 77 aserciones por técnica, principalmente ejemplos pequeños, y requiere casos borde/ocultos más amplios para estimar generalización.

**Importante sobre la versión del tratamiento:** la corrida ya completada utilizó la plantilla versión 1 y la instrucción CoT anterior, que pedía un resumen del análisis pese a la regla común de responder solo con código. La plantilla actual es versión 2 y elimina esa contradicción. La versión y el hash del prompt están incluidos en los metadatos y en las exportaciones; no se deben agregar ambas versiones en un mismo análisis sin estratificarlas. Para una comparación de tesis, se recomienda definir una nueva versión de protocolo y repetir todas las técnicas con varias réplicas y una batería funcional/benchmark ampliada, preservando esta línea base sin sobrescribirla.

## 7. Corrida v2 en `investigacionv2`

La repetición de la matriz se guardó en una base separada con el protocolo `EXP-2026-GPT4O-02`: 30 problemas × 4 técnicas = **120/120 ejecuciones completadas**, una repetición por combinación, modelo reportado `gpt-4o-2024-08-06`, temperatura 0.0 y plantilla v2. Los 120 hashes de prompt son distintos y cada registro conserva modelo, parámetros y tokens. El uso total fue 123,261 tokens de entrada y 22,480 de salida; el costo estimado con tarifas públicas fue **USD 0.5330**, dentro del tope aprobado de USD 5. No es una factura del proveedor.

| Técnica | Aserciones aprobadas / 77 | Aprobación de aserciones | Ejecuciones que aprobaron todas las pruebas |
| :--- | ---: | ---: | ---: |
| Zero-Shot | 56 | 72.7% | 17/30 (56.7%) |
| Few-Shot | 58 | 75.3% | 20/30 (66.7%) |
| Chain-of-Thought v2 | 57 | 74.0% | 18/30 (60.0%) |
| Role Prompting | 57 | 74.0% | 18/30 (60.0%) |
| **Total** | **228/308** | **74.0%** | **73/120 (60.8%)** |

Por dificultad, aprobaron todas las pruebas 34/40 ejecuciones fáciles, 23/40 medias y 16/40 difíciles. Los resultados aún son descriptivos y no demuestran superioridad de Few-Shot ni mejoras causadas por la plantilla v2. Comparada con v1, la aprobación completa pasó de 71/120 (59.2%) a 73/120 (60.8%); la diferencia de dos ejecuciones, con una sola repetición y solicitudes en momentos distintos, no permite atribuir causalidad.

El benchmark v2 produjo 1,200 mediciones sobre el primer caso funcional: 830 válidas y 370 fallidas; 83/120 ejecuciones tuvieron al menos una medición válida y 37 no tuvieron ninguna. El promedio de los promedios por ejecución válidos fue 0.1922 ms y la mediana de tiempos medianos fue 0.1733 ms. Como en v1, no representa entradas grandes ni complejidad asintótica.

En siete problemas (LC-4055, LC-4076, LC-4077, LC-4086, LC-4090, LC-4091 y LC-4095) ninguna de las cuatro técnicas aprobó todos los casos funcionales registrados. Esto identifica casos que conviene inspeccionar manualmente y reforzar con pruebas independientes; por sí solo no permite distinguir entre una limitación del modelo, errores en los casos de prueba o ambigüedad en la especificación.

**Separación de datos:** la base `investigacion` conserva la línea base v1. La aplicación local ahora apunta a `investigacionv2` y al protocolo `EXP-2026-GPT4O-02`; las exportaciones incluyen el protocolo, versión de plantilla y hash de prompt para prevenir mezclas accidentales.
