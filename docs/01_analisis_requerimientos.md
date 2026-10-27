# Documento 01: Análisis de Requerimientos del Sistema
## Plataforma de Investigación Experimental (Prompt Engineering Research Lab)

**Tesis:** *Técnicas de Estructuración de Prompts en la Calidad de Código Generado por el Modelo de Lenguaje de Gran Escala ChatGPT-4o*  
**Metodología:** Cascada Adaptada (Fase 1: Análisis)  
**Versión:** 1.0.0  
**Fecha:** 2026-10-26  
**Autor:** Ingeniero de Software Principal / Investigador Principal  

---

## 1. Introducción y Propósito

El presente documento formaliza los Requerimientos Funcionales (RF) y No Funcionales (RNF) para la plataforma experimental automatizada diseñada para contrastar empíricamente la efectividad de cuatro técnicas de estructuración de prompts (**Zero-Shot**, **Few-Shot**, **Chain-of-Thought [CoT]** y **Role Prompting**) en la generación de código algorítmico utilizando el modelo de lenguaje de gran escala **ChatGPT-4o** (`gpt-4o`) de OpenAI.

La plataforma proporciona un entorno estandarizado, determinista e inmutable para la ingesta de problemas algorítmicos (LeetCode), la construcción dinámica de prompts, la invocación de la API de OpenAI, y la posterior evaluación multifacética del código generado en tres dimensiones fundamentales:
1. **Exactitud Funcional** (Testing de conformidad con Pytest).
2. **Mantenibilidad del Código** (Métricas de Radon: Maintainability Index [MI], Complejidad Ciclomática [CC], SLOC/LOC).
3. **Eficiencia de Desempeño** (Tiempo de ejecución en milisegundos vía `timeit` y consumo de memoria pico vía `tracemalloc`).

---

## 2. Requerimientos Funcionales (RF)

### 2.1 Ingesta y Gestión de Problemas Algorítmicos

- **RF-01: Registro y Edición de Problemas:**
  El sistema debe permitir registrar y modificar problemas algorítmicos provenientes de LeetCode u otras plataformas, incluyendo:
  - Código único (`codigo`, ej. `LC-001`).
  - Título (`titulo`).
  - Dificultad categórica (`dificultad`: *Fácil*, *Media*, *Difícil*).
  - Categoría algorítmica (`categoria_algoritmica`, ej. *Arreglos, Programación Dinámica, Grafos, Hash Table*).
  - Enunciado descriptivo (`enunciado`).
  - Restricciones computacionales y de dominio (`restricciones`).
  - Solución de referencia opcional (`solucion_referencia`).

- **RF-02: Segregación Estricta de Ejemplos y Pruebas (Integridad de Datos):**
  Para evitar contaminación de datos y garantizar la validez experimental, el sistema debe segregar explícitamente en el esquema de base de datos y la interfaz de usuario:
  1. `ejemplos_enunciado`: Ejemplos contextuales que forman parte del problema original oficial (entradas, salidas y explicaciones).
  2. `ejemplos_few_shot`: Demostraciones resueltas reservadas exclusivamente para la técnica de *Few-Shot Prompting*, las cuales no deben mezclarse con los casos de prueba ni con el enunciado base.
  3. `pruebas_funcionales`: Casos de prueba unitarios automatizados que se ejecutarán con Pytest para evaluar la solución generada por el LLM.

- **RF-03: Gestión Dinámica de Demostraciones Few-Shot:**
  El sistema debe proveer una interfaz dinámica para agregar, editar y eliminar ejemplos de demostración Few-Shot (par entrada/salida y código/explicación), calculando de forma automática `cantidad_ejemplos_few_shot`.

---

### 2.2 Motor de Construcción de Prompts y Gestión de Protocolos

- **RF-04: Catálogo de Técnicas de Prompting:**
  El sistema debe admitir las cuatro técnicas objeto de estudio con sus respectivos identificadores normalizados:
  - `ZERO_SHOT`: Instrucción directa sin demostraciones.
  - `FEW_SHOT`: Inyección ordenada de demostraciones de código resueltas.
  - `CHAIN_OF_THOUGHT`: Directrices que obligan al modelo a razonar paso a paso antes de entregar la implementación final.
  - `ROLE_PROMPTING`: Imposición de un perfil de Ingeniero de Software Principal y especialista en algoritmos avanzados de Python.

- **RF-05: Interpolación de Plantillas de Prompts:**
  El sistema debe almacenar plantillas versionadas (`plantilla_prompt`) vinculadas a cada técnica y al protocolo experimental activo (`protocolo_experimental`), permitiendo generar el prompt final mediante interpolación segura de variables (`{titulo}`, `{dificultad}`, `{categoria}`, `{enunciado}`, `{restricciones}`, `{ejemplos_enunciado}`, `{ejemplos_few_shot_bloque}`).

- **RF-06: Previsualización en Tiempo Real:**
  La interfaz debe permitir previsualizar en tiempo real el prompt exacto que será enviado a la API de inferencia antes de iniciar la corrida experimental.

---

### 2.3 Capa de Integración con OpenAI (ChatGPT-4o)

- **RF-07: Invocación Oficial de la API de OpenAI:**
  El sistema debe conectarse a la API oficial de OpenAI mediante cliente asíncrono configurado con la clave de entorno `OPENAI_API_KEY`.
  - Modelo objetivo: `gpt-4o`.
  - Parámetro de temperatura mandatorio: `temperature=0.0` (Greedy Decoding) para garantizar respuestas deterministas y reproducibles.
  - Configuración opcional de fallback de simulación/modo de prueba en caso de fallos de red o pruebas locales sin consumo de cuota.

- **RF-08: Limpieza y Extracción Automatizada de Código (`clean_code_block`):**
  El sistema debe procesar la respuesta íntegra del modelo mediante una función de extracción robusta (`clean_code_block()`) que:
  - Aísle el bloque de código Python delimitado por ` ```python ... ``` ` o comillas triples genéricas.
  - Remueva texto conversacional, preámbulos explicativos o notas de cierre generadas en CoT o Role Prompting.
  - Verifique la sintaxis mediante `ast.parse()`, asignando la bandera `codigo_parseable`.

- **RF-09: Trazabilidad y Hashing Criptográfico:**
  Para cada llamada a la API, el sistema debe:
  - Calcular y registrar el hash SHA-256 del código extraído (`hash_codigo_sha256`) para auditoría de inmutabilidad y detección de determinismo.
  - Registrar la latencia total de respuesta en milisegundos (`duracion_generacion_ms`).
  - Conservar el prompt enviado (`prompt_enviado`) y la respuesta cruda íntegra (`respuesta_completa`).

---

### 2.4 Módulo de Evaluación Automatizada y Perfilamiento

- **RF-10: Evaluación de Exactitud Funcional con Pytest:**
  - El sistema debe materializar dinámicamente un archivo de prueba temporal que combine el código generado por el LLM con los casos de prueba definidos en `pruebas_funcionales`.
  - Debe ejecutar Pytest en un subproceso aislado, capturando el estado de cada prueba individual (`aprobada`, `fallida`, `error`, `timeout`), la duración en milisegundos, y el mensaje de error/traceback en caso de aserción fallida.
  - Registrar individualmente cada aserción en `resultado_prueba`.

- **RF-11: Análisis Estático y Mantenibilidad con Radon:**
  - **Maintainability Index (MI):** Calcular el índice de mantenibilidad (escala 0-100) del código generado.
  - **Complejidad Ciclomática (CC):** Calcular la complejidad ciclomática de McCabe a nivel global de módulo y desglosada por cada función en la tabla `complejidad_funcion`.
  - **Métricas de Tamaño:** Extraer Líneas de Código (LOC), Líneas de Código Fuente (SLOC), comentarios y líneas en blanco.

- **RF-12: Perfilamiento de Eficiencia de Desempeño:**
  - **Tiempo de Ejecución (Runtime):** Ejecutar mediciones mediante el módulo estándar `timeit`, implementando una fase inicial de calentamiento (*warm-up* de 3 corridas) seguida de repeticiones cronometradas (10 repeticiones de medición). Cada corrida debe registrarse en `benchmark_corrida`.
  - **Memoria Máxima (Peak Memory):** Medir el pico de memoria asignada en tiempo de ejecución utilizando el módulo `tracemalloc`, registrando el valor en bytes y convirtiéndolo a Kilobytes (KB) y Megabytes (MB).
  - Los tiempos y memorias deben tabularse desagregadamente en `benchmark_corrida` y consolidarse en `medicion_metrica`.

---

### 2.5 Consultas Analíticas, Visualización y Exportación

- **RF-13: Consulta de Vistas Relacionales:**
  El sistema debe consultar en tiempo real las vistas relacionales de PostgreSQL:
  - `vw_resumen_pruebas`: Total de pruebas, aprobadas, fallidas, y porcentaje consolidado.
  - `vw_resumen_benchmark`: Tiempos promedio, mediano, mínimo, máximo y memoria mediana.

- **RF-14: Matriz Comparativa Interactiva:**
  La interfaz debe presentar una tabla comparativa con ordenamiento, filtrado por problema y técnica, resaltando las diferencias de rendimiento y calidad de código entre las 4 técnicas de prompting.

- **RF-15: Exportación de Datos para Análisis Estadístico:**
  El sistema debe permitir descargar la matriz consolidada de mediciones en formatos **CSV** y **JSON**, listos para su análisis estadístico posterior en R, Python/Pandas o SPSS (pruebas de hipótesis, ANOVA, Kruskal-Wallis).

---

## 3. Requerimientos No Funcionales (RNF)

- **RNF-01: Determinismo y Reproducibilidad Experimental:**
  - Parámetro de inferencia estricto `temperature=0.0`.
  - Auditoría de hashes SHA-256 entre réplicas experimentales.
  - Registro explícito de metadatos del entorno (Versión de Python 3.14, SO Arch Linux x86_64, versión de librerías).

- **RNF-02: Regla Estricta de Integridad de Datos Científicos:**
  - Separación absoluta entre mediciones crudas (`benchmark_corrida`, `resultado_prueba`, `complejidad_funcion`) y valores agregados (`medicion_metrica`, vistas).
  - **Regla mandatoria:** Si una métrica no puede ser calculada debido a error de sintaxis, timeout o falla de ejecución, el valor numérico DEBE registrarse como `NULL` o documentarse en `estado_medicion` (`no_disponible`, `error`). **NUNCA** debe convertirse o imputarse un fallo como `0`, para no sesgar las medias y análisis estadísticos de la investigación.

- **RNF-03: Seguridad y Aislamiento de Ejecución:**
  - La ejecución de código generado por LLM debe realizarse en procesos secundarios con límites de tiempo (*timeouts* configurables de 5 a 10 segundos) para prevenir bucles infinitos o ataques de denegación de servicio accidental.

- **RNF-04: Rendimiento y Latencia:**
  - La API del backend (FastAPI) debe ser completamente asíncrona, utilizando `asyncpg` / `SQLAlchemy Async` para no bloquear el bucle de eventos durante consultas pesadas.
  - La evaluación de Radon y Pytest debe procesarse sin degradar la respuesta visual de la plataforma.

- **RNF-05: Usabilidad y Estética Visual de Nivel Superior (UI/UX):**
  - Interfaz web moderna, intuitiva y profesional basada en componentes reactivos, paleta de colores armónica en modo oscuro (Dark Mode moderno con acentos cian, índigo y violeta), tipografía legible (`Inter` / `Fira Code`) y retroalimentación interactiva instantánea.
  - Presentación clara de código con sintaxis resaltada y visores diferenciados para prompt, respuesta del LLM y código extraído.

- **RNF-06: Modularidad y Mantenibilidad del Código:**
  - Arquitectura modular desacoplada: Servicios independientes para OpenAI, Pytest Runner, Radon Analyzer, y Benchmark Profiler.

---

## 4. Matriz de Trazabilidad de Requerimientos

| Requerimiento | Componente Asociado | Módulo / Tabla BD | Criterio de Aceptación |
| :--- | :--- | :--- | :--- |
| **RF-01** | Frontend Ingesta / Backend API | `problema` | CRUD de problemas LeetCode operativo. |
| **RF-02** | Frontend Ingesta / BD Schema | `ejemplos_enunciado`, `ejemplos_few_shot`, `pruebas_funcionales` | Columnas independientes en JSONB con validación `array`. |
| **RF-03** | Frontend Ingesta | `ejemplos_few_shot` | Controles dinámicos para añadir demostraciones. |
| **RF-04** | Backend Engine | `tecnica_prompt` | 4 técnicas preconfiguradas con códigos normalizados. |
| **RF-05** | Backend Prompt Service | `plantilla_prompt` | Renderizado determinista de plantillas por técnica. |
| **RF-06** | Frontend Ejecución | API `/api/prompts/preview` | Visualización en vivo del prompt antes de enviar. |
| **RF-07** | OpenAI Service | `ejecucion_experimental` | Conexión `gpt-4o`, `temperature=0.0`. |
| **RF-08** | Ingestion & Parser | `codigo_generado`, `codigo_parseable` | Extracción vía regex y validación con `ast.parse()`. |
| **RF-09** | Backend Security | `hash_codigo_sha256`, `duracion_generacion_ms` | Generación de SHA-256 de 64 caracteres hex. |
| **RF-10** | Pytest Evaluator | `resultado_prueba`, `vw_resumen_pruebas` | Captura de estado de aserciones individuales en BD. |
| **RF-11** | Radon Evaluator | `medicion_metrica`, `complejidad_funcion` | Cálculo de MI, CC módulo/función y SLOC. |
| **RF-12** | Benchmark Profiler | `benchmark_corrida`, `vw_resumen_benchmark` | Calentamiento (3) + Mediciones (10), timeit + tracemalloc. |
| **RF-13** | Backend Analytics | `vw_resumen_pruebas`, `vw_resumen_benchmark` | Endpoints REST consultando las vistas SQL. |
| **RF-14** | Frontend Resultados | Interfaz 3 | Tabla comparativa consolidada con filtros. |
| **RF-15** | Export Service | API `/api/export/{csv,json}` | Descarga de datasets normalizados para análisis estadístico. |
