# Documento 02: Diseño de Arquitectura del Sistema
## Plataforma de Investigación Experimental (Prompt Engineering Research Lab)

**Tesis:** *Técnicas de Estructuración de Prompts en la Calidad de Código Generado por el Modelo de Lenguaje de Gran Escala ChatGPT-4o*  
**Metodología:** Cascada Adaptada (Fase 2: Diseño)  
**Versión:** 1.0.0  
**Fecha:** 2026-10-26  
**Autor:** Ingeniero de Software Principal / Arquitecto de Software  

---

## 1. Visión Arquitectónica General

La plataforma experimental adopta una arquitectura en capas desacopladas orientada a servicios (Layered Service-Oriented Architecture), diseñada específicamente para garantizar:
- **Reproducibilidad y Determinismo Experimental:** Inferencia estricta con `temperature=0.0`, trazabilidad criptográfica mediante hashes SHA-256 de cada artefacto generado.
- **Aislamiento en la Ejecución:** Los módulos de evaluación funcional (Pytest) y de rendimiento (`timeit`, `tracemalloc`) operan en entornos de ejecución controlados para mitigar interferencias del sistema operativo o efectos colaterales de código generado.
- **Integridad de Datos Científicos:** Desacoplamiento estricto entre mediciones en crudo (corridas individuales de benchmark y aserciones unitarias) y métricas agregadas sintetizadas en vistas relacionales de PostgreSQL.

```
+-----------------------------------------------------------------------------------+
|                           CAPA DE PRESENTACIÓN (FRONTEND)                         |
|   +--------------------------+  +--------------------------+  +-------------------+
|   | Interfaz 1: Ingesta      |  | Interfaz 2: Ejecución    |  | Interfaz 3:       |
|   | y Gestión de Problemas   |  | Experimental en Vivo     |  | Matriz Comparativa|
|   +--------------------------+  +--------------------------+  +-------------------+
+-----------------------------------------|-----------------------------------------+
                                          | HTTP / JSON REST APIs
+-----------------------------------------v-----------------------------------------+
|                         CAPA DE CONTROL Y APLICACIÓN (FASTAPI)                     |
|   +--------------------------+  +--------------------------+  +-------------------+
|   | Router de Problemas      |  | Router de Ejecuciones    |  | Router de Métricas|
|   +--------------------------+  +--------------------------+  +-------------------+
+-----------------------------------------|-----------------------------------------+
                                          |
+-----------------------------------------v-----------------------------------------+
|                               CAPA DE SERVICIOS CORE                              |
|  +------------------+  +-------------------+  +---------------+  +---------------+|
|  | PromptBuilder    |  | OpenAIService     |  | CodeExtractor |  | EventLogger   ||
|  | Service          |  | (ChatGPT-4o, T=0) |  | (clean/AST)   |  | Service       ||
|  +------------------+  +-------------------+  +---------------+  +---------------+|
|  +-------------------------------------------------------------------------------+|
|  |                     PIPELINE DE EVALUACIÓN MULTI-DIMENSIONAL                   ||
|  |  +---------------------+  +---------------------+  +------------------------+  ||
|  |  | FunctionalEvaluator |  | MaintainabilityEval |  | PerformanceBenchmark   |  ||
|  |  | (Pytest Runner)     |  | (Radon MI, CC, LOC) |  | (timeit + tracemalloc) |  ||
|  |  +---------------------+  +---------------------+  +------------------------+  ||
|  +-------------------------------------------------------------------------------+|
+-----------------------------------------|-----------------------------------------+
                                          | SQLAlchemy Async / asyncpg
+-----------------------------------------v-----------------------------------------+
|                         CAPA DE PERSISTENCIA (POSTGRESQL 18)                      |
|                               Esquema "experimento"                               |
|   +--------------------------+  +--------------------------+  +-------------------+
|   | Tablas Operacionales     |  | Tablas de Medición Cruda |  | Vistas Analíticas |
|   | (problema, ejecucion,    |  | (resultado_prueba,       |  | (vw_resumen_      |
|   | protocolo, tecnica, ...) |  | benchmark_corrida, ...)  |  | pruebas / bench)  |
|   +--------------------------+  +--------------------------+  +-------------------+
+-----------------------------------------------------------------------------------+
```

---

## 2. Diagrama de Componentes

El siguiente diagrama detalla la interacción entre los componentes del Frontend, la API del Backend, los evaluadores especializados y la base de datos relacional.

```mermaid
graph TD
    subgraph Frontend ["Frontend Web Application (SPA)"]
        UI_Prob["Módulo de Gestión de Problemas<br/>(Enunciado + Few-Shot + Pruebas)"]
        UI_Exec["Módulo de Ejecución Experimental<br/>(Selector Técnica + Visor en Vivo)"]
        UI_Matrix["Módulo Matriz Comparativa<br/>(Dashboard Métricas + Exportador)"]
    end

    subgraph Backend ["Backend API Service (FastAPI)"]
        API_Gateway["API Router & Endpoints"]
        PB["Prompt Builder Service<br/>(Zero-Shot, Few-Shot, CoT, Role)"]
        LLM_Client["OpenAI Client Service<br/>(gpt-4o, temperature=0.0)"]
        Cleaner["Code Extractor & AST Parser<br/>(clean_code_block + SHA-256)"]
        
        subgraph EvalEngine ["Motor de Evaluación Automatizada"]
            Pytest_Mod["Pytest Evaluator<br/>(Aislamiento de subproceso)"]
            Radon_Mod["Radon Static Analyzer<br/>(MI, CC Módulo/Función, SLOC)"]
            Bench_Mod["Benchmark Profiler<br/>(timeit warm-up + tracemalloc peak)"]
        end
        
        Repo["Data Access Layer<br/>(SQLAlchemy Async / asyncpg)"]
    end

    subgraph External ["Servicios Externos"]
        OAI["OpenAI REST API<br/>(Endpoint /v1/chat/completions)"]
    end

    subgraph Database ["Base de Datos Relacional (PostgreSQL 18)"]
        DB_Schema[("Esquema 'experimento'<br/>11 Tablas Relacionales<br/>2 Vistas Analíticas")]
    end

    UI_Prob -->|CRUD /api/problemas| API_Gateway
    UI_Exec -->|POST /api/ejecutar| API_Gateway
    UI_Matrix -->|GET /api/metricas| API_Gateway
    
    API_Gateway --> PB
    PB --> LLM_Client
    LLM_Client -->|Solicitud gpt-4o T=0.0| OAI
    OAI -->|Respuesta LLM| LLM_Client
    LLM_Client --> Cleaner
    Cleaner --> EvalEngine
    
    Pytest_Mod --> Repo
    Radon_Mod --> Repo
    Bench_Mod --> Repo
    Cleaner --> Repo
    API_Gateway --> Repo
    Repo --> DB_Schema
```

---

## 3. Diagrama de Flujo de Datos y Pipeline Experimental

El flujo de procesamiento para cada ejecución individual sigue una secuencia lineal e inmutable:

```mermaid
sequenceDiagram
    autonumber
    actor Inv as Investigador
    participant UI as Frontend (SPA)
    participant API as Backend (FastAPI)
    participant PB as PromptBuilder
    participant OAI as OpenAI API (gpt-4o)
    participant CE as CodeExtractor
    participant EV as Evaluation Pipeline
    participant DB as PostgreSQL (experimento)

    Inv->>UI: Selecciona Problema y Técnica (ej. CoT)
    UI->>API: POST /api/experimento/ejecutar {problema_id, tecnica_id}
    API->>DB: Registra ejecucion_experimental (estado: 'en_proceso')
    API->>PB: Construir Prompt según Técnica y Plantilla
    PB-->>API: Prompt interpolado final
    API->>OAI: chat.completions.create(model='gpt-4o', temp=0.0)
    OAI-->>API: Respuesta íntegra y tokens (latencia_ms)
    API->>CE: clean_code_block(respuesta_cruda)
    CE-->>API: codigo_extraido, parseable_bool, sha256_hash
    API->>DB: Actualiza ejecucion (codigo, prompt, sha256, latencia)
    
    par Evaluación Funcional
        API->>EV: Ejecutar Pytest (pruebas_funcionales)
        EV->>DB: Inserta resultado_prueba (por cada aserción)
    and Análisis Estático
        API->>EV: Ejecutar Radon (MI, CC, LOC/SLOC)
        EV->>DB: Inserta complejidad_funcion y medicion_metrica
    and Perfilamiento de Rendimiento
        API->>EV: Ejecutar timeit (calentamiento 3 + corridas 10) & tracemalloc
        EV->>DB: Inserta benchmark_corrida (por cada repetición)
    end

    API->>DB: Actualiza ejecucion (estado: 'completada', estado_validacion: 'valido')
    API-->>UI: Retorna payload consolidado con métricas y código
    UI->>Inv: Renderiza Prompt, Respuesta, Código y Métricas en Pantalla
```

---

## 4. Modelo Entidad-Relación de la Base de Datos

El diseño del esquema relacional `experimento` implementa una separación estricta entre definición de problemas, configuración del protocolo, ejecuciones y mediciones empíricas.

```mermaid
erDiagram
    PROTOCOLO_EXPERIMENTAL ||--o{ PLANTILLA_PROMPT : define
    PROTOCOLO_EXPERIMENTAL ||--o{ EJECUCION_EXPERIMENTAL : rige
    TECNICA_PROMPT ||--o{ PLANTILLA_PROMPT : tipifica
    TECNICA_PROMPT ||--o{ EJECUCION_EXPERIMENTAL : categoriza
    PROBLEMA ||--o{ EJECUCION_EXPERIMENTAL : evalua
    
    EJECUCION_EXPERIMENTAL ||--o{ RESULTADO_PRUEBA : produce
    EJECUCION_EXPERIMENTAL ||--o{ EJECUCION_HERRAMIENTA : registra
    EJECUCION_EXPERIMENTAL ||--o{ MEDICION_METRICA : genera
    EJECUCION_EXPERIMENTAL ||--o{ BENCHMARK_CORRIDA : mide
    EJECUCION_EXPERIMENTAL ||--o{ COMPLEJIDAD_FUNCION : desglosa
    EJECUCION_EXPERIMENTAL ||--o{ REGISTRO_EVENTO : audita
    
    EJECUCION_HERRAMIENTA ||--o{ MEDICION_METRICA : origina
    EJECUCION_HERRAMIENTA ||--o{ BENCHMARK_CORRIDA : origina
    EJECUCION_HERRAMIENTA ||--o{ COMPLEJIDAD_FUNCION : origina

    PROTOCOLO_EXPERIMENTAL {
        bigint protocolo_id PK
        text codigo UK
        text titulo
        text modelo_objetivo
        text lenguaje
        text version_python
        text sistema_operativo
        text entorno_evaluacion
        jsonb configuracion_global
        boolean activo
    }

    TECNICA_PROMPT {
        smallint tecnica_id PK
        text codigo UK
        text nombre UK
        text descripcion
        boolean requiere_ejemplos
        boolean activa
    }

    PROBLEMA {
        bigint problema_id PK
        text codigo UK
        text titulo
        text plataforma_origen
        text dificultad
        text categoria_algoritmica
        text enunciado
        text restricciones
        jsonb ejemplos_enunciado
        jsonb ejemplos_few_shot
        smallint cantidad_ejemplos_few_shot
        text solucion_referencia
        jsonb pruebas_funcionales
        text[] etiquetas
    }

    PLANTILLA_PROMPT {
        bigint plantilla_id PK
        bigint protocolo_id FK
        smallint tecnica_id FK
        text nombre
        integer version_plantilla
        text plantilla_texto
        jsonb reglas_formateo
    }

    EJECUCION_EXPERIMENTAL {
        bigint ejecucion_id PK
        bigint protocolo_id FK
        bigint problema_id FK
        smallint tecnica_id FK
        bigint plantilla_id FK
        integer numero_repeticion
        text estado_ejecucion
        numeric duracion_generacion_ms
        text prompt_enviado
        text respuesta_completa
        text codigo_generado
        char hash_codigo_sha256
        boolean codigo_parseable
        boolean generacion_exitosa
        text estado_validacion
    }

    RESULTADO_PRUEBA {
        bigint resultado_prueba_id PK
        bigint ejecucion_id FK
        text identificador_prueba
        text tipo_prueba
        text estado
        numeric duracion_ms
        jsonb entrada
        jsonb salida_esperada
        jsonb salida_obtenida
        text mensaje_error
    }

    EJECUCION_HERRAMIENTA {
        bigint herramienta_ejecucion_id PK
        bigint ejecucion_id FK
        text tipo_analisis
        text herramienta
        text version_herramienta
        text comando
        text estado
        integer codigo_salida
        text stdout
        text stderr
    }

    MEDICION_METRICA {
        bigint medicion_id PK
        bigint ejecucion_id FK
        bigint herramienta_ejecucion_id FK
        text dimension
        text indicador
        text metrica
        text alcance
        text elemento_codigo
        numeric valor_numerico
        text valor_texto
        text unidad
        text estado_medicion
    }

    BENCHMARK_CORRIDA {
        bigint benchmark_id PK
        bigint ejecucion_id FK
        integer numero_corrida
        text tipo_corrida
        text conjunto_entrada
        boolean resultado_correcto
        numeric tiempo_ejecucion_ms
        bigint memoria_pico_bytes
        boolean timeout
    }

    COMPLEJIDAD_FUNCION {
        bigint complejidad_id PK
        bigint ejecucion_id FK
        text nombre_funcion
        text nombre_clase
        integer linea_inicio
        integer linea_fin
        integer complejidad_ciclomatica
        numeric complejidad_cognitiva
    }

    REGISTRO_EVENTO {
        bigint evento_id PK
        bigint ejecucion_id FK
        text nivel
        text componente
        text evento
        text mensaje
        timestamptz ocurrido_en
    }
```

---

## 5. Diccionario y Reglas del Esquema

1. **Protocolo Inmutable (`protocolo_experimental`):** Establece el marco experimental científico. Registra las versiones exactas del hardware, kernel y entorno evaluador (ej. Arch Linux, Python 3.14).
2. **Segregación de Ejemplos en `problema`:**
   - `ejemplos_enunciado`: Ejemplos contextuales para comprensión del problema.
   - `ejemplos_few_shot`: Casos de demostración (código/explicación) inyectados **únicamente** en la técnica Few-Shot.
   - `pruebas_funcionales`: Conjunto de aserciones automatizadas Pytest para evaluación de exactitud.
3. **Métricas Crudas vs Agregadas:**
   - La tabla `benchmark_corrida` preserva cada repetición individual de medición (separando corridas de `calentamiento` de las de `medicion`).
   - La tabla `resultado_prueba` preserva el estatus y tiempo de cada aserción Pytest.
   - La vista `vw_resumen_pruebas` computa en tiempo de ejecución `% pruebas aprobadas`.
   - La vista `vw_resumen_benchmark` computa tiempos promedio, mediano, mínimo, máximo y memoria mediana sin imputaciones arbitrarias.
4. **Regla de Integridad de Fallas:** Si un código no compila o produce error en tiempo de ejecución, el campo `valor_numerico` en `medicion_metrica` se conserva como `NULL` y el campo `estado_medicion` se etiqueta como `error` o `no_disponible`. **Nunca se escribe 0** para evitar sesgos en el análisis de varianza estadístico.
