-- Esquema relacional para la plataforma experimental de generación y evaluación de código.
-- Compatible con PostgreSQL 14+ (se recomienda una versión soportada reciente).
-- Ejecutar conectado a la base de datos que se desea utilizar:
--   psql -U postgres -d nombre_base -f esquema_experimental.sql
--
-- Este archivo crea el esquema "experimento" y sus tablas, índices, restricciones y vistas.
-- No crea roles, contraseñas ni la base de datos; esas operaciones dependen de la instalación.
-- Zona horaria recomendada para la sesión: UTC. Los timestamps se guardan como timestamptz.

BEGIN;

CREATE SCHEMA IF NOT EXISTS experimento;
SET search_path TO experimento, public;

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
 ('ZERO_SHOT', 'Zero-shot', 'Instrucción sin ejemplos de solución incluidos en el prompt.', FALSE),
 ('FEW_SHOT', 'Few-shot', 'Instrucción que incorpora uno o más ejemplos de entrada/salida o de solución.', TRUE),
 ('CHAIN_OF_THOUGHT', 'Chain-of-Thought', 'Instrucción que solicita razonamiento estructurado antes de presentar la solución.', FALSE),
 ('ROLE_PROMPTING', 'Role prompting', 'Instrucción que asigna un rol o perfil al modelo antes de resolver el problema.', FALSE)
ON CONFLICT (codigo) DO NOTHING;

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
    -- Campo específico para ejemplos que se incorporarán en la técnica few-shot.
    -- Mantenerlo separado de los ejemplos del enunciado evita mezclar datos de prueba
    -- con ejemplos de demostración entregados al LLM.
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
    parametros_modelo      JSONB NOT NULL DEFAULT '{}'::jsonb,
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

-- Vistas de resumen: mantienen separadas las medidas crudas de los agregados.
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
    COUNT(*) FILTER (WHERE tipo_corrida = 'medicion' AND NOT timeout AND codigo_salida = 0) AS corridas_validas,
    ROUND(AVG(tiempo_ejecucion_ms) FILTER (WHERE tipo_corrida = 'medicion' AND NOT timeout AND codigo_salida = 0), 6) AS tiempo_promedio_ms,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY tiempo_ejecucion_ms)
        FILTER (WHERE tipo_corrida = 'medicion' AND NOT timeout AND codigo_salida = 0) AS tiempo_mediano_ms,
    MIN(tiempo_ejecucion_ms) FILTER (WHERE tipo_corrida = 'medicion' AND NOT timeout AND codigo_salida = 0) AS tiempo_minimo_ms,
    MAX(tiempo_ejecucion_ms) FILTER (WHERE tipo_corrida = 'medicion' AND NOT timeout AND codigo_salida = 0) AS tiempo_maximo_ms,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY memoria_pico_bytes)
        FILTER (WHERE tipo_corrida = 'medicion' AND NOT timeout AND codigo_salida = 0 AND memoria_pico_bytes IS NOT NULL) AS memoria_mediana_bytes
FROM benchmark_corrida
GROUP BY ejecucion_id, conjunto_entrada;

COMMIT;

-- Notas de uso:
-- 1. Guarde el código generado y el prompt completo en ejecucion_experimental.
-- 2. Registre cada prueba individual en resultado_prueba; no almacene solo el porcentaje.
-- 3. Registre stdout, stderr, versión de herramienta y configuración en ejecucion_herramienta.
-- 4. Use benchmark_corrida para cada repetición; separe calentamiento y medición.
-- 5. Use medicion_metrica para MI, LOC/SLOC, porcentaje de pruebas, tiempos agregados,
--    memoria y métricas complementarias. Guarde también valores por función en complejidad_funcion.
-- 6. No sustituya NULL por cero cuando una métrica no pudo calcularse: marque el estado.
-- 7. El contenido de ejemplos_few_shot es distinto de ejemplos_enunciado y pruebas_funcionales.
