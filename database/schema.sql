-- ============================================================================
-- PLATAFORMA DE INVESTIGACIÓN EXPERIMENTAL: PROMPT ENGINEERING RESEARCH LAB
-- Tesis: Técnicas de Estructuración de Prompts en la Calidad de Código 
--        Generado por el Modelo de Lenguaje de Gran Escala ChatGPT-4o
-- Esquema relacional compatible con PostgreSQL 14+
-- ============================================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS experimento;
SET search_path TO experimento, public;

-- ----------------------------------------------------------------------------
-- 1. PROTOCOLO EXPERIMENTAL
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS protocolo_experimental (
    protocolo_id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo                 TEXT NOT NULL UNIQUE,
    titulo                 TEXT NOT NULL,
    objetivo               TEXT,
    modelo_objetivo        TEXT NOT NULL DEFAULT 'ChatGPT-4o',
    lenguaje               TEXT NOT NULL DEFAULT 'Python',
    version_python         TEXT NOT NULL DEFAULT '3.14',
    sistema_operativo      TEXT NOT NULL DEFAULT 'Arch Linux',
    entorno_evaluacion     TEXT NOT NULL DEFAULT 'Arch Linux',
    descripcion_diseno     TEXT,
    configuracion_global   JSONB NOT NULL DEFAULT '{}'::jsonb,
    fecha_creacion         TIMESTAMPTZ NOT NULL DEFAULT now(),
    activo                 BOOLEAN NOT NULL DEFAULT TRUE
);

-- ----------------------------------------------------------------------------
-- 2. TÉCNICA DE PROMPT
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tecnica_prompt (
    tecnica_id             SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo                 TEXT NOT NULL UNIQUE,
    nombre                 TEXT NOT NULL UNIQUE,
    descripcion            TEXT,
    requiere_ejemplos      BOOLEAN NOT NULL DEFAULT FALSE,
    activa                 BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (codigo = upper(codigo))
);

INSERT INTO tecnica_prompt (codigo, nombre, descripcion, requiere_ejemplos)
VALUES
 ('ZERO_SHOT', 'Zero-shot', 'Instrucción directa sin ejemplos de demostración de código en el prompt.', FALSE),
 ('FEW_SHOT', 'Few-shot', 'Instrucción que incorpora demostraciones explícitas de entrada/salida y código.', TRUE),
 ('CHAIN_OF_THOUGHT', 'Chain-of-Thought', 'Instrucción que solicita razonamiento paso a paso antes de producir el bloque final.', FALSE),
 ('ROLE_PROMPTING', 'Role prompting', 'Instrucción que asigna un perfil de Ingeniero de Software Principal experto al modelo.', FALSE)
ON CONFLICT (codigo) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 3. PROBLEMA / EJERCICIO LEETCODE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS problema (
    problema_id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo                 TEXT NOT NULL UNIQUE,
    titulo                 TEXT NOT NULL,
    plataforma_origen      TEXT NOT NULL CHECK (plataforma_origen IN ('LeetCode','HackerRank','Otro','Propio')),
    url_referencia         TEXT,
    dificultad             TEXT NOT NULL CHECK (dificultad IN ('Fácil','Media','Difícil','No aplica')),
    categoria_algoritmica  TEXT,
    enunciado              TEXT NOT NULL,
    especificacion_entrada TEXT,
    especificacion_salida  TEXT,
    restricciones          TEXT,
    ejemplos_enunciado     JSONB NOT NULL DEFAULT '[]'::jsonb,
    -- Ejemplos reservados para inyección en prompt Few-Shot
    ejemplos_few_shot      JSONB NOT NULL DEFAULT '[]'::jsonb,
    cantidad_ejemplos_few_shot SMALLINT NOT NULL DEFAULT 0 CHECK (cantidad_ejemplos_few_shot >= 0),
    solucion_referencia    TEXT,
    pruebas_funcionales    JSONB NOT NULL DEFAULT '[]'::jsonb,
    etiquetas              TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    metadatos              JSONB NOT NULL DEFAULT '{}'::jsonb,
    version_problema       INTEGER NOT NULL DEFAULT 1 CHECK (version_problema > 0),
    activo                 BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en              TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en         TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (jsonb_typeof(ejemplos_enunciado) = 'array'),
    CHECK (jsonb_typeof(ejemplos_few_shot) = 'array'),
    CHECK (jsonb_typeof(pruebas_funcionales) = 'array')
);

-- ----------------------------------------------------------------------------
-- 4. PLANTILLA DE PROMPT
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS plantilla_prompt (
    plantilla_id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    protocolo_id           BIGINT NOT NULL REFERENCES protocolo_experimental(protocolo_id),
    tecnica_id             SMALLINT NOT NULL REFERENCES tecnica_prompt(tecnica_id),
    nombre                 TEXT NOT NULL,
    version_plantilla      INTEGER NOT NULL DEFAULT 1 CHECK (version_plantilla > 0),
    plantilla_texto        TEXT NOT NULL,
    reglas_formateo        JSONB NOT NULL DEFAULT '{}'::jsonb,
    activa                 BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en              TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (protocolo_id, tecnica_id, nombre, version_plantilla)
);

-- ----------------------------------------------------------------------------
-- 5. EJECUCIÓN EXPERIMENTAL (Registro individual de corrida)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ejecucion_experimental (
    ejecucion_id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    protocolo_id           BIGINT NOT NULL REFERENCES protocolo_experimental(protocolo_id),
    problema_id            BIGINT NOT NULL REFERENCES problema(problema_id),
    tecnica_id             SMALLINT NOT NULL REFERENCES tecnica_prompt(tecnica_id),
    plantilla_id           BIGINT REFERENCES plantilla_prompt(plantilla_id),
    numero_repeticion      INTEGER NOT NULL DEFAULT 1 CHECK (numero_repeticion > 0),
    identificador_externo  TEXT UNIQUE,
    estado_ejecucion       TEXT NOT NULL DEFAULT 'pendiente'
        CHECK (estado_ejecucion IN ('pendiente','en_proceso','completada','fallida','cancelada','excluida')),
    fecha_inicio           TIMESTAMPTZ,
    fecha_fin              TIMESTAMPTZ,
    duracion_generacion_ms NUMERIC(14,3) CHECK (duracion_generacion_ms IS NULL OR duracion_generacion_ms >= 0),
    modelo_reportado       TEXT NOT NULL DEFAULT 'ChatGPT-4o',
    identificador_modelo   TEXT,
    parametros_modelo      JSONB NOT NULL DEFAULT '{"model": "gpt-4o", "temperature": 0.0}'::jsonb,
    prompt_enviado         TEXT,
    respuesta_completa     TEXT,
    codigo_generado        TEXT,
    hash_codigo_sha256     CHAR(64),
    codigo_parseable       BOOLEAN,
    generacion_exitosa     BOOLEAN,
    estado_validacion      TEXT NOT NULL DEFAULT 'no_evaluado'
        CHECK (estado_validacion IN ('no_evaluado','valido','parcial','invalido','error_entorno','no_aplicable')),
    motivo_exclusion       TEXT,
    observaciones          TEXT,
    metadatos              JSONB NOT NULL DEFAULT '{}'::jsonb,
    creado_en              TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (protocolo_id, problema_id, tecnica_id, numero_repeticion),
    CHECK (fecha_fin IS NULL OR fecha_inicio IS NULL OR fecha_fin >= fecha_inicio)
);

CREATE INDEX IF NOT EXISTS idx_ejecucion_problema ON ejecucion_experimental(problema_id);
CREATE INDEX IF NOT EXISTS idx_ejecucion_tecnica ON ejecucion_experimental(tecnica_id);
CREATE INDEX IF NOT EXISTS idx_ejecucion_estado ON ejecucion_experimental(estado_ejecucion);
CREATE INDEX IF NOT EXISTS idx_ejecucion_metadata ON ejecucion_experimental USING GIN (metadatos);

-- ----------------------------------------------------------------------------
-- 6. RESULTADOS DE PRUEBAS UNITARIAS (Pytest)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS resultado_prueba (
    resultado_prueba_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ejecucion_id           BIGINT NOT NULL REFERENCES ejecucion_experimental(ejecucion_id) ON DELETE CASCADE,
    identificador_prueba   TEXT NOT NULL,
    tipo_prueba            TEXT NOT NULL DEFAULT 'funcional',
    estado                 TEXT NOT NULL CHECK (estado IN ('aprobada','fallida','error','omitida','timeout','no_ejecutada')),
    duracion_ms            NUMERIC(14,3) CHECK (duracion_ms IS NULL OR duracion_ms >= 0),
    entrada                JSONB,
    salida_esperada         JSONB,
    salida_obtenida         JSONB,
    mensaje_error          TEXT,
    traceback              TEXT,
    log_salida             TEXT,
    metadatos              JSONB NOT NULL DEFAULT '{}'::jsonb,
    creado_en              TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (ejecucion_id, identificador_prueba)
);

CREATE INDEX IF NOT EXISTS idx_resultado_prueba_ejecucion ON resultado_prueba(ejecucion_id);
CREATE INDEX IF NOT EXISTS idx_resultado_prueba_estado ON resultado_prueba(estado);

-- ----------------------------------------------------------------------------
-- 7. EJECUCIÓN DE HERRAMIENTAS (Metadatos de Radon, Pytest, Timeit)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ejecucion_herramienta (
    herramienta_ejecucion_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ejecucion_id           BIGINT NOT NULL REFERENCES ejecucion_experimental(ejecucion_id) ON DELETE CASCADE,
    tipo_analisis          TEXT NOT NULL CHECK (tipo_analisis IN ('analisis_estatico','benchmark','pruebas','lint','seguridad','otro')),
    herramienta            TEXT NOT NULL,
    version_herramienta    TEXT,
    comando                TEXT,
    estado                 TEXT NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente','ejecutando','completado','fallido','omitido','error_entorno')),
    fecha_inicio           TIMESTAMPTZ,
    fecha_fin              TIMESTAMPTZ,
    codigo_salida          INTEGER,
    stdout                 TEXT,
    stderr                 TEXT,
    log_completo           TEXT,
    error_resumen          TEXT,
    entorno                JSONB NOT NULL DEFAULT '{}'::jsonb,
    resultado_bruto        JSONB NOT NULL DEFAULT '{}'::jsonb,
    creado_en              TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (fecha_fin IS NULL OR fecha_inicio IS NULL OR fecha_fin >= fecha_inicio)
);

CREATE INDEX IF NOT EXISTS idx_herramienta_ejecucion ON ejecucion_herramienta(ejecucion_id);
CREATE INDEX IF NOT EXISTS idx_herramienta_tipo ON ejecucion_herramienta(tipo_analisis);

-- ----------------------------------------------------------------------------
-- 8. MEDICIÓN DE MÉTRICAS (Mantenibilidad, Desempeño, Exactitud)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS medicion_metrica (
    medicion_id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ejecucion_id           BIGINT NOT NULL REFERENCES ejecucion_experimental(ejecucion_id) ON DELETE CASCADE,
    herramienta_ejecucion_id BIGINT REFERENCES ejecucion_herramienta(herramienta_ejecucion_id) ON DELETE SET NULL,
    dimension              TEXT NOT NULL CHECK (dimension IN ('exactitud_funcional','mantenibilidad','eficiencia_desempeno','complementaria')),
    indicador              TEXT NOT NULL,
    metrica                TEXT NOT NULL,
    alcance                TEXT NOT NULL DEFAULT 'modulo'
        CHECK (alcance IN ('modulo','funcion','metodo','archivo','proceso','prueba','global')),
    elemento_codigo        TEXT,
    valor_numerico         NUMERIC(20,6),
    valor_texto            TEXT,
    unidad                 TEXT,
    escala_interpretacion  TEXT,
    estado_medicion        TEXT NOT NULL DEFAULT 'valida'
        CHECK (estado_medicion IN ('valida','no_disponible','error','no_aplicable','excluida')),
    metodo_calculo         TEXT,
    observaciones          TEXT,
    datos_adicionales      JSONB NOT NULL DEFAULT '{}'::jsonb,
    medido_en              TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (valor_numerico IS NOT NULL OR valor_texto IS NOT NULL OR estado_medicion <> 'valida')
);

CREATE INDEX IF NOT EXISTS idx_medicion_ejecucion ON medicion_metrica(ejecucion_id);
CREATE INDEX IF NOT EXISTS idx_medicion_dimension_metrica ON medicion_metrica(dimension, metrica);

-- ----------------------------------------------------------------------------
-- 9. BENCHMARK CORRIDA (Tiempo y Memoria: calentamiento y repeticiones)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS benchmark_corrida (
    benchmark_id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ejecucion_id           BIGINT NOT NULL REFERENCES ejecucion_experimental(ejecucion_id) ON DELETE CASCADE,
    herramienta_ejecucion_id BIGINT REFERENCES ejecucion_herramienta(herramienta_ejecucion_id) ON DELETE SET NULL,
    numero_corrida         INTEGER NOT NULL CHECK (numero_corrida > 0),
    tipo_corrida           TEXT NOT NULL CHECK (tipo_corrida IN ('calentamiento','medicion')),
    conjunto_entrada       TEXT NOT NULL,
    semilla                BIGINT,
    resultado_correcto     BOOLEAN,
    tiempo_ejecucion_ms    NUMERIC(16,6) CHECK (tiempo_ejecucion_ms IS NULL OR tiempo_ejecucion_ms >= 0),
    memoria_pico_bytes     BIGINT CHECK (memoria_pico_bytes IS NULL OR memoria_pico_bytes >= 0),
    timeout                BOOLEAN NOT NULL DEFAULT FALSE,
    codigo_salida          INTEGER,
    stdout                 TEXT,
    stderr                 TEXT,
    detalles               JSONB NOT NULL DEFAULT '{}'::jsonb,
    iniciado_en            TIMESTAMPTZ,
    finalizado_en          TIMESTAMPTZ,
    CHECK (finalizado_en IS NULL OR iniciado_en IS NULL OR finalizado_en >= iniciado_en),
    UNIQUE (ejecucion_id, conjunto_entrada, numero_corrida, tipo_corrida)
);

CREATE INDEX IF NOT EXISTS idx_benchmark_ejecucion ON benchmark_corrida(ejecucion_id);

-- ----------------------------------------------------------------------------
-- 10. COMPLEJIDAD CICLOMÁTICA Y COGNITIVA POR FUNCIÓN
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS complejidad_funcion (
    complejidad_id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ejecucion_id           BIGINT NOT NULL REFERENCES ejecucion_experimental(ejecucion_id) ON DELETE CASCADE,
    herramienta_ejecucion_id BIGINT REFERENCES ejecucion_herramienta(herramienta_ejecucion_id) ON DELETE SET NULL,
    nombre_funcion         TEXT NOT NULL,
    nombre_clase           TEXT,
    linea_inicio           INTEGER,
    linea_fin              INTEGER,
    complejidad_ciclomatica INTEGER CHECK (complejidad_ciclomatica IS NULL OR complejidad_ciclomatica >= 0),
    complejidad_cognitiva  NUMERIC(12,4) CHECK (complejidad_cognitiva IS NULL OR complejidad_cognitiva >= 0),
    datos_adicionales      JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_complejidad_ejecucion ON complejidad_funcion(ejecucion_id);

-- ----------------------------------------------------------------------------
-- 11. REGISTRO DE EVENTOS (Auditoría y Trazabilidad)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS registro_evento (
    evento_id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ejecucion_id           BIGINT REFERENCES ejecucion_experimental(ejecucion_id) ON DELETE CASCADE,
    nivel                  TEXT NOT NULL CHECK (nivel IN ('DEBUG','INFO','WARNING','ERROR','CRITICAL')),
    componente             TEXT NOT NULL,
    evento                 TEXT NOT NULL,
    mensaje                TEXT NOT NULL,
    detalle_error          TEXT,
    traceback              TEXT,
    datos                  JSONB NOT NULL DEFAULT '{}'::jsonb,
    ocurrido_en            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_evento_ejecucion ON registro_evento(ejecucion_id);
CREATE INDEX IF NOT EXISTS idx_evento_nivel_fecha ON registro_evento(nivel, ocurrido_en);
CREATE INDEX IF NOT EXISTS idx_evento_datos ON registro_evento USING GIN (datos);

-- ----------------------------------------------------------------------------
-- 12. VISTAS ANALÍTICAS CONSOLIDADAS
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_resumen_pruebas AS
SELECT
    e.ejecucion_id,
    e.problema_id,
    e.tecnica_id,
    COUNT(r.resultado_prueba_id) FILTER (WHERE r.tipo_prueba = 'funcional') AS pruebas_registradas,
    COUNT(r.resultado_prueba_id) FILTER (WHERE r.tipo_prueba = 'funcional' AND r.estado = 'aprobada') AS pruebas_aprobadas,
    COUNT(r.resultado_prueba_id) FILTER (WHERE r.tipo_prueba = 'funcional' AND r.estado = 'fallida') AS pruebas_fallidas,
    COUNT(r.resultado_prueba_id) FILTER (WHERE r.tipo_prueba = 'funcional' AND r.estado IN ('error','timeout')) AS pruebas_con_error,
    CASE
      WHEN COUNT(r.resultado_prueba_id) FILTER (WHERE r.tipo_prueba = 'funcional') > 0
      THEN ROUND(
        100.0 * COUNT(r.resultado_prueba_id) FILTER (WHERE r.tipo_prueba = 'funcional' AND r.estado = 'aprobada')
        / COUNT(r.resultado_prueba_id) FILTER (WHERE r.tipo_prueba = 'funcional'), 2)
      ELSE NULL
    END AS porcentaje_pruebas_aprobadas
FROM ejecucion_experimental e
LEFT JOIN resultado_prueba r ON r.ejecucion_id = e.ejecucion_id
GROUP BY e.ejecucion_id, e.problema_id, e.tecnica_id;

CREATE OR REPLACE VIEW vw_resumen_benchmark AS
SELECT
    ejecucion_id,
    conjunto_entrada,
    COUNT(*) FILTER (WHERE tipo_corrida = 'medicion' AND NOT timeout AND (codigo_salida = 0 OR codigo_salida IS NULL)) AS corridas_validas,
    ROUND(AVG(tiempo_ejecucion_ms) FILTER (WHERE tipo_corrida = 'medicion' AND NOT timeout AND (codigo_salida = 0 OR codigo_salida IS NULL)), 6) AS tiempo_promedio_ms,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY tiempo_ejecucion_ms)
        FILTER (WHERE tipo_corrida = 'medicion' AND NOT timeout AND (codigo_salida = 0 OR codigo_salida IS NULL)) AS tiempo_mediano_ms,
    MIN(tiempo_ejecucion_ms) FILTER (WHERE tipo_corrida = 'medicion' AND NOT timeout AND (codigo_salida = 0 OR codigo_salida IS NULL)) AS tiempo_minimo_ms,
    MAX(tiempo_ejecucion_ms) FILTER (WHERE tipo_corrida = 'medicion' AND NOT timeout AND (codigo_salida = 0 OR codigo_salida IS NULL)) AS tiempo_maximo_ms,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY memoria_pico_bytes)
        FILTER (WHERE tipo_corrida = 'medicion' AND NOT timeout AND (codigo_salida = 0 OR codigo_salida IS NULL) AND memoria_pico_bytes IS NOT NULL) AS memoria_mediana_bytes
FROM benchmark_corrida
GROUP BY ejecucion_id, conjunto_entrada;

-- ----------------------------------------------------------------------------
-- 13. SEED INICIAL: PROTOCOLO EXPERIMENTAL POR DEFECTO Y PLANTILLAS
-- ----------------------------------------------------------------------------
INSERT INTO protocolo_experimental (codigo, titulo, objetivo, modelo_objetivo, lenguaje, version_python, sistema_operativo, entorno_evaluacion, descripcion_diseno, configuracion_global)
VALUES (
    'EXP-2026-GPT4O-01',
    'Protocolo de Evaluación Empírica de Técnicas de Prompting en ChatGPT-4o',
    'Evaluar el impacto de Zero-Shot, Few-Shot, CoT y Role Prompting en la exactitud funcional, mantenibilidad y eficiencia de algoritmos generados por ChatGPT-4o.',
    'ChatGPT-4o',
    'Python',
    '3.14',
    'Arch Linux x86_64',
    'Arch Linux (Kernel 6.x, Python 3.14, Pytest, Radon, timeit, tracemalloc)',
    'Diseño experimental factorial con réplicas controladas bajo Greedy Decoding (temperature=0.0).',
    '{"temperatura": 0.0, "semilla_determinismo": 42, "repeticiones_benchmark": 10, "calentamiento_benchmark": 3}'::jsonb
)
ON CONFLICT (codigo) DO NOTHING;

-- Plantillas base de prompts para cada técnica
INSERT INTO plantilla_prompt (protocolo_id, tecnica_id, nombre, version_plantilla, plantilla_texto, reglas_formateo)
SELECT 
    p.protocolo_id,
    t.tecnica_id,
    'Plantilla Estándar ' || t.nombre,
    1,
    CASE t.codigo
        WHEN 'ZERO_SHOT' THEN 
'Escribe una solución en Python 3 para el siguiente problema algorítmico:

Título: {titulo}
Dificultad: {dificultad}
Categoría: {categoria}

Enunciado:
{enunciado}

Restricciones:
{restricciones}

Ejemplos oficiales del enunciado:
{ejemplos_enunciado}

Instrucciones de formato:
1. Proporciona una solución limpia, correcta y eficiente en Python 3.
2. Encapsula la solución en la clase o función solicitada.
3. Responde únicamente con el bloque de código Python entre comillas triples ```python ... ``` sin texto adicional.'

        WHEN 'FEW_SHOT' THEN
'A continuación se presentan ejemplos resueltos de referencia para ilustrar el estilo de implementación esperado:

{ejemplos_few_shot_bloque}

Ahora, resuelve el siguiente problema en Python 3:

Título: {titulo}
Dificultad: {dificultad}
Categoría: {categoria}

Enunciado:
{enunciado}

Restricciones:
{restricciones}

Ejemplos oficiales del enunciado:
{ejemplos_enunciado}

Instrucciones de formato:
1. Proporciona una solución limpia, modular y eficiente en Python 3.
2. Encapsula la solución según la estructura esperada.
3. Responde únicamente con el bloque de código Python entre comillas triples ```python ... ``` sin texto explicativo posterior.'

        WHEN 'CHAIN_OF_THOUGHT' THEN
'Analiza y resuelve paso a paso el siguiente problema algorítmico en Python 3:

Título: {titulo}
Dificultad: {dificultad}
Categoría: {categoria}

Enunciado:
{enunciado}

Restricciones:
{restricciones}

Ejemplos oficiales:
{ejemplos_enunciado}

Estructura de razonamiento requerida:
Paso 1: Comprensión del problema y casos borde (edge cases).
Paso 2: Análisis de complejidad temporal y espacial requerida.
Paso 3: Diseño algorítmico y estructura de datos elegida.
Paso 4: Implementación del código final optimizado.

Al final, entrega la implementación definitiva encerrada en un bloque de código Markdown ```python ... ```.'

        WHEN 'ROLE_PROMPTING' THEN
'Eres un Ingeniero de Software Principal y especialista en algoritmos avanzados de estructuras de datos y optimización de código en Python. Tu código se caracteriza por:
- Máxima claridad y legibilidad (alta mantenibilidad y bajo acoplamiento).
- Baja complejidad ciclomática por función.
- Eficiencia óptima en tiempo de ejecución O(n) o minimalista y uso restringido de memoria.
- Riguroso manejo de precondiciones y restricciones.

Resuelve el siguiente problema con los más altos estándares de calidad:

Título: {titulo}
Dificultad: {dificultad}
Categoría: {categoria}

Enunciado:
{enunciado}

Restricciones:
{restricciones}

Ejemplos oficiales:
{ejemplos_enunciado}

Entrega el código Python definitivo encapsulado en un bloque ```python ... ```.'
    END,
    '{"requiere_bloque_markdown": true, "temperatura": 0.0}'::jsonb
FROM protocolo_experimental p
CROSS JOIN tecnica_prompt t
WHERE p.codigo = 'EXP-2026-GPT4O-01'
ON CONFLICT (protocolo_id, tecnica_id, nombre, version_plantilla) DO NOTHING;

COMMIT;
