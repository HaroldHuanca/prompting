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
