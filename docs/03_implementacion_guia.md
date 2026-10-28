# Documento 03: Guía de Implementación y Estructura del Proyecto
## Plataforma de Investigación Experimental (Prompt Engineering Research Lab)

**Tesis:** *Técnicas de Estructuración de Prompts en la Calidad de Código Generado por el Modelo de Lenguaje de Gran Escala ChatGPT-4o*  
**Metodología:** Cascada Adaptada (Fase 3: Implementación)  
**Versión:** 1.0.0  
**Fecha:** 2026-10-26  
**Autor:** Ingeniero de Software Principal  

---

## 1. Estructura de Directorios del Proyecto

La plataforma sigue una organización modular limpia, separando frontend estático enriquecido, backend API en FastAPI, servicios de evaluación especializados, scripts de base de datos y documentación:

```
prompting/
├── database/
│   ├── schema.sql                 # DDL relacional completo (Esquema 'experimento', tablas y vistas)
│   └── seed_problems.sql          # Inserción de problemas LeetCode canónicos con pruebas y Few-Shot
├── docs/
│   ├── 01_analisis_requerimientos.md   # Requerimientos Funcionales y No Funcionales
│   ├── 02_diseno_arquitectura.md       # Diagramas de componentes, flujos y modelo E-R
│   ├── 03_implementacion_guia.md       # Estructura del proyecto, .env y API Endpoints
│   └── 04_pruebas_y_validacion.md      # Protocolo de pruebas, integración y determinismo T=0.0
├── backend/
│   ├── config.py                  # Parámetros globales y carga de variables de entorno (.env)
│   ├── database.py                # Conexión SQLAlchemy / asyncpg y utilitarios de sesión
│   ├── schemas.py                 # Modelos Pydantic para validación de entrada/salida REST
│   ├── main.py                    # Aplicación FastAPI, configuración CORS y montaje estático
│   ├── services/
│   │   ├── openai_service.py      # Cliente oficial de OpenAI (gpt-4o, temperature=0.0)
│   │   ├── prompt_builder.py      # Constructor de prompts para las 4 técnicas
│   │   ├── code_extractor.py      # Extracción clean_code_block, validación AST y hash SHA-256
│   │   ├── evaluators/
│   │   │   ├── pytest_evaluator.py     # Ejecución y captura de pruebas unitarias Pytest
│   │   │   ├── radon_evaluator.py      # Análisis estático Radon (MI, CC, LOC/SLOC)
│   │   │   └── benchmark_evaluator.py  # Perfilamiento timeit (warmup + runs) y tracemalloc
│   │   └── export_service.py      # Generador de exportaciones a formato CSV y JSON
│   └── routers/
│       ├── problemas.py           # CRUD de problemas con segregación Few-Shot / pruebas
│       ├── ejecuciones.py         # Orquestación de corridas experimentales en tiempo real
│       ├── metricas.py            # Consultas agregadas sobre vw_resumen_pruebas y benchmark
│       └── export.py              # Endpoints para descarga de datasets analíticos
├── frontend/
│   ├── index.html                 # Aplicación SPA con 3 paneles funcionales
│   ├── styles.css                 # Sistema de diseño moderno (Dark Mode, Glassmorphism)
│   └── app.js                     # Controlador reactivo en Vanilla JS para interacción fluida
├── .env.example                   # Plantilla de variables de entorno
└── .env                           # Variables de entorno locales configuradas
```

---

## 2. Configuración de Variables de Entorno (`.env`)

El archivo `.env` en la raíz del proyecto contiene los parámetros esenciales:

```ini
# Configuración del Entorno de Investigación Experimental
ENVIRONMENT=development
LOG_LEVEL=INFO

# Conexión a Base de Datos PostgreSQL
DATABASE_URL=postgresql+asyncpg://postgres@localhost:5432/investigacionv2
DATABASE_SYNC_URL=postgresql://postgres@localhost:5432/investigacionv2

# OpenAI API Configuration
OPENAI_API_KEY=tu_clave_de_openai_aqui
TARGET_MODEL=gpt-4o
TEMPERATURE=0.0

# Parámetros del Protocolo de Evaluación Experimental
CODIGO_PROTOCOLO=EXP-2026-GPT4O-02
BENCHMARK_WARMUP_RUNS=3
BENCHMARK_MEASURE_RUNS=10
EXECUTION_TIMEOUT_SECONDS=5.0
```

---

## 3. Catálogo de API Endpoints (FastAPI)

### 3.1 Gestión de Problemas (`/api/problemas`)

| Método | Endpoint | Descripción | Payload / Parámetros |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/problemas` | Lista todos los problemas registrados | Filtro opcional `?dificultad=Media` |
| `GET` | `/api/problemas/{id}` | Obtiene el detalle completo del problema | `id` (bigint) |
| `POST` | `/api/problemas` | Registra un nuevo problema con separación estricta | JSON con `enunciado`, `ejemplos_enunciado`, `ejemplos_few_shot`, `pruebas_funcionales` |
| `PUT` | `/api/problemas/{id}` | Actualiza un problema existente | JSON parcial o completo |
| `DELETE` | `/api/problemas/{id}` | Desactiva o elimina un problema | `id` (bigint) |

### 3.2 Construcción y Previsualización de Prompts (`/api/prompts`)

| Método | Endpoint | Descripción | Payload / Parámetros |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/prompts/preview` | Genera y previsualiza el prompt sin ejecutarlo | `{"problema_id": 1, "tecnica_codigo": "FEW_SHOT"}` |
| `GET` | `/api/tecnicas` | Lista las 4 técnicas disponibles con metadatos | Ninguno |

### 3.3 Orquestación Experimental (`/api/ejecuciones`)

| Método | Endpoint | Descripción | Payload / Parámetros |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/ejecutar` | Inicia una corrida experimental completa (LLM + Evaluación) | `{"problema_id": 1, "tecnica_codigo": "CHAIN_OF_THOUGHT", "repeticion": 1}` |
| `GET` | `/api/ejecuciones` | Lista el historial de ejecuciones realizadas | Filtros opcionales por problema y técnica |
| `GET` | `/api/ejecuciones/{id}` | Obtiene el detalle de una ejecución, su código y métricas | `id` (bigint) |

### 3.4 Matriz Comparativa y Métricas (`/api/metricas`)

| Método | Endpoint | Descripción | Payload / Parámetros |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/metricas/matriz` | Consulta consolidada de `vw_resumen_pruebas` y `vw_resumen_benchmark` | `?problema_id=1` |
| `GET` | `/api/metricas/pruebas/{ejecucion_id}` | Detalle de aserciones unitarias Pytest | `ejecucion_id` |
| `GET` | `/api/metricas/complejidad/{ejecucion_id}` | Detalle de complejidad Radon por función | `ejecucion_id` |
| `GET` | `/api/metricas/benchmark/{ejecucion_id}` | Corridas crudas de tiempo y memoria | `ejecucion_id` |

### 3.5 Exportación de Datos Científicos (`/api/export`)

| Método | Endpoint | Descripción | Salida |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/export/csv` | Descarga de la matriz comparativa consolidada | Archivo `dataset_experimental_prompting.csv` |
| `GET` | `/api/export/json` | Descarga estructurada completa para R / Python Pandas | Archivo `dataset_experimental_prompting.json` |

---

## 4. Instrucciones de Despliegue y Ejecución Local

1. **Configuración del entorno virtual e instalación:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install fastapi uvicorn[standard] pytest radon openai asyncpg sqlalchemy python-dotenv httpx psycopg2-binary
   ```

2. **Inicialización de la Base de Datos:**
   ```bash
   psql -U postgres -d investigacionv2 -f database/schema.sql
   psql -U postgres -d investigacionv2 -f database/seed_problems.sql
   ```

3. **Ejecución del Servidor de la Plataforma:**
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Acceso a la Interfaz Web:**
   Abrir en el navegador: `http://localhost:8000`
