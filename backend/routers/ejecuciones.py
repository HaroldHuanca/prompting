"""
Router de Orquestación y Ejecución Experimental.
Coordina:
1. Construcción del Prompt
2. Inferencia ChatGPT-4o (T=0.0)
3. Extracción de Código y Hash SHA-256
4. Evaluación Funcional (Pytest)
5. Análisis Estático (Radon)
6. Perfilamiento de Rendimiento (timeit + tracemalloc)
7. Persistencia Desagregada en PostgreSQL
"""
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.database import fetch_all, fetch_one, execute_dml
from backend.schemas import (
    TecnicaResponse,
    PromptPreviewRequest,
    PromptPreviewResponse,
    ExecutionRequest,
    ExecutionResponse,
    ResultadoPruebaItem,
    ComplejidadItem,
    BenchmarkItem
)
from backend.services.prompt_builder import build_prompt
from backend.services.openai_service import OpenAIService
from backend.services.code_extractor import clean_code_block
from backend.services.evaluators.pytest_evaluator import evaluate_functional_tests
from backend.services.evaluators.radon_evaluator import evaluate_code_maintainability
from backend.services.evaluators.benchmark_evaluator import evaluate_benchmark
from backend.config import CODIGO_PROTOCOLO

router = APIRouter(prefix="/api", tags=["Ejecución Experimental"])
openai_service = OpenAIService()

@router.get("/tecnicas", response_model=List[TecnicaResponse])
async def list_tecnicas():
    """Lista las técnicas de Prompt Engineering disponibles en el protocolo."""
    rows = await fetch_all("SELECT tecnica_id, codigo, nombre, descripcion, requiere_ejemplos FROM tecnica_prompt WHERE activa = TRUE ORDER BY tecnica_id ASC;")
    return rows

@router.post("/prompts/preview", response_model=PromptPreviewResponse)
async def preview_prompt(req: PromptPreviewRequest):
    """Previsualiza en tiempo real el prompt exacto antes de ser enviado a ChatGPT-4o."""
    prob = await fetch_one("SELECT * FROM problema WHERE problema_id = :id AND activo = TRUE", {"id": req.problema_id})
    if not prob:
        raise HTTPException(status_code=404, detail="Problema no encontrado")

    tec = await fetch_one("SELECT * FROM tecnica_prompt WHERE codigo = :cod", {"cod": req.tecnica_codigo.upper()})
    if not tec:
        raise HTTPException(status_code=404, detail=f"Técnica {req.tecnica_codigo} no encontrada")

    prompt_data = build_prompt(prob, tec["codigo"])

    return PromptPreviewResponse(
        problema_id=prob["problema_id"],
        problema_titulo=prob["titulo"],
        tecnica_codigo=tec["codigo"],
        tecnica_nombre=tec["nombre"],
        prompt=prompt_data["prompt"],
        variables=prompt_data["variables"]
    )

@router.post("/ejecutar", response_model=ExecutionResponse)
async def execute_experiment(req: ExecutionRequest):
    """
    Ejecuta el pipeline experimental completo:
    Inferencia determinista T=0.0 -> Extracción -> Pytest -> Radon -> Benchmark -> Persistencia.
    """
    # 1. Obtener protocolo activo
    proto = await fetch_one("SELECT protocolo_id FROM protocolo_experimental WHERE codigo = :cod AND activo = TRUE", {"cod": CODIGO_PROTOCOLO})
    if not proto:
        proto = await fetch_one("SELECT protocolo_id FROM protocolo_experimental WHERE activo = TRUE LIMIT 1")
    proto_id = proto["protocolo_id"] if proto else 1

    # 2. Obtener problema y técnica
    prob = await fetch_one("SELECT * FROM problema WHERE problema_id = :id AND activo = TRUE", {"id": req.problema_id})
    if not prob:
        raise HTTPException(status_code=404, detail="Problema no encontrado")

    tec = await fetch_one("SELECT * FROM tecnica_prompt WHERE codigo = :cod", {"cod": req.tecnica_codigo.upper()})
    if not tec:
        raise HTTPException(status_code=404, detail=f"Técnica {req.tecnica_codigo} no encontrada")

    # 3. Construir prompt formal
    prompt_obj = build_prompt(prob, tec["codigo"])
    prompt_text = prompt_obj["prompt"]

    # 4. Registrar ejecución en estado 'en_proceso'
    insert_exec_sql = """
        INSERT INTO ejecucion_experimental (
            protocolo_id, problema_id, tecnica_id, numero_repeticion,
            estado_ejecucion, fecha_inicio, fecha_fin, modelo_reportado, prompt_enviado
        ) VALUES (
            :protocolo_id, :problema_id, :tecnica_id, :numero_repeticion,
            'en_proceso', now(), NULL, 'ChatGPT-4o', :prompt_enviado
        )
        ON CONFLICT (protocolo_id, problema_id, tecnica_id, numero_repeticion)
        DO UPDATE SET
            estado_ejecucion = 'en_proceso',
            fecha_inicio = now(),
            fecha_fin = NULL,
            prompt_enviado = EXCLUDED.prompt_enviado
        RETURNING ejecucion_id;
    """
    exec_row = await fetch_one(insert_exec_sql, {
        "protocolo_id": proto_id,
        "problema_id": prob["problema_id"],
        "tecnica_id": tec["tecnica_id"],
        "numero_repeticion": req.numero_repeticion,
        "prompt_enviado": prompt_text,
    })
    ejecucion_id = exec_row["ejecucion_id"]

    # 5. Inferencia con ChatGPT-4o (temperature=0.0)
    llm_result = await openai_service.generate_solution(prompt_text, prob, tec["codigo"])
    respuesta_completa = llm_result["respuesta_completa"]
    duracion_ms = llm_result["duracion_ms"]

    # 6. Extracción automatizada de código y hash SHA-256
    codigo_limpio, es_parseable, hash_sha256 = clean_code_block(respuesta_completa)

    # 7. Evaluación de Exactitud Funcional (Pytest)
    pruebas_raw = prob.get("pruebas_funcionales") or []
    if isinstance(pruebas_raw, str):
        pruebas_raw = json.loads(pruebas_raw)
    
    pytest_res = evaluate_functional_tests(codigo_limpio, pruebas_raw)

    # Limpiar resultados anteriores de esta ejecución para evitar duplicados en re-ejecuciones
    await execute_dml("DELETE FROM resultado_prueba WHERE ejecucion_id = :id", {"id": ejecucion_id})
    await execute_dml("DELETE FROM complejidad_funcion WHERE ejecucion_id = :id", {"id": ejecucion_id})
    await execute_dml("DELETE FROM benchmark_corrida WHERE ejecucion_id = :id", {"id": ejecucion_id})
    await execute_dml("DELETE FROM medicion_metrica WHERE ejecucion_id = :id", {"id": ejecucion_id})

    # Insertar aserciones individuales en resultado_prueba
    for r in pytest_res["resultados_detalle"]:
        await execute_dml("""
            INSERT INTO resultado_prueba (
                ejecucion_id, identificador_prueba, tipo_prueba, estado,
                duracion_ms, mensaje_error, traceback
            ) VALUES (
                :ejecucion_id, :identificador, :tipo, :estado,
                :duracion, :mensaje, :tb
            )
        """, {
            "ejecucion_id": ejecucion_id,
            "identificador": r["identificador_prueba"],
            "tipo": r["tipo_prueba"],
            "estado": r["estado"],
            "duracion": r["duracion_ms"],
            "mensaje": r["mensaje_error"],
            "tb": r["traceback"],
        })

    # Guardar métrica consolidada de pruebas
    await execute_dml("""
        INSERT INTO medicion_metrica (
            ejecucion_id, dimension, indicador, metrica, alcance, valor_numerico, unidad, estado_medicion
        ) VALUES (
            :id, 'exactitud_funcional', 'pruebas_unitarias', 'porcentaje_pruebas_aprobadas', 'modulo',
            :val, '%', :estado
        )
    """, {
        "id": ejecucion_id,
        "val": pytest_res["porcentaje_aprobadas"],
        "estado": "valida" if pytest_res["porcentaje_aprobadas"] is not None else "error"
    })

    # 8. Evaluación de Mantenibilidad (Radon)
    radon_res = evaluate_code_maintainability(codigo_limpio)
    
    for f in radon_res["funciones"]:
        await execute_dml("""
            INSERT INTO complejidad_funcion (
                ejecucion_id, nombre_funcion, nombre_clase, linea_inicio, linea_fin, complejidad_ciclomatica
            ) VALUES (
                :id, :nombre, :clase, :inicio, :fin, :cc
            )
        """, {
            "id": ejecucion_id,
            "nombre": f["nombre_funcion"],
            "clase": f["nombre_clase"],
            "inicio": f["linea_inicio"],
            "fin": f["linea_fin"],
            "cc": f["complejidad_ciclomatica"],
        })

    # Registrar Maintainability Index (MI)
    await execute_dml("""
        INSERT INTO medicion_metrica (
            ejecucion_id, dimension, indicador, metrica, alcance, valor_numerico, unidad, escala_interpretacion, estado_medicion
        ) VALUES (
            :id, 'mantenibilidad', 'indice_mantenibilidad', 'maintainability_index', 'modulo',
            :val, 'puntos', '0-100', :estado
        )
    """, {
        "id": ejecucion_id,
        "val": radon_res["maintainability_index"],
        "estado": "valida" if radon_res["maintainability_index"] is not None else "error"
    })

    # Registrar Complejidad Ciclomática Máxima
    await execute_dml("""
        INSERT INTO medicion_metrica (
            ejecucion_id, dimension, indicador, metrica, alcance, valor_numerico, unidad, estado_medicion
        ) VALUES (
            :id, 'mantenibilidad', 'complejidad_mccabe', 'complejidad_ciclomatica_max', 'modulo',
            :val, 'rutas', :estado
        )
    """, {
        "id": ejecucion_id,
        "val": radon_res["complejidad_ciclomatica_max"],
        "estado": "valida" if radon_res["complejidad_ciclomatica_max"] is not None else "error"
    })

    # Registrar SLOC
    await execute_dml("""
        INSERT INTO medicion_metrica (
            ejecucion_id, dimension, indicador, metrica, alcance, valor_numerico, unidad, estado_medicion
        ) VALUES (
            :id, 'mantenibilidad', 'tamano_codigo', 'sloc', 'modulo',
            :val, 'lineas', :estado
        )
    """, {
        "id": ejecucion_id,
        "val": radon_res["sloc"],
        "estado": "valida" if radon_res["sloc"] is not None else "error"
    })

    # 9. Evaluación de Rendimiento y Memoria (Benchmark Profiler)
    bench_res = evaluate_benchmark(codigo_limpio, pruebas_raw)

    for c in bench_res["corridas"]:
        await execute_dml("""
            INSERT INTO benchmark_corrida (
                ejecucion_id, numero_corrida, tipo_corrida, conjunto_entrada,
                resultado_correcto, tiempo_ejecucion_ms, memoria_pico_bytes, timeout, codigo_salida
            ) VALUES (
                :id, :num, :tipo, :entrada, :ok, :tiempo, :mem, :tout, :cod
            )
        """, {
            "id": ejecucion_id,
            "num": c["numero_corrida"],
            "tipo": c["tipo_corrida"],
            "entrada": c["conjunto_entrada"],
            "ok": c["resultado_correcto"],
            "tiempo": c["tiempo_ejecucion_ms"],
            "mem": c["memoria_pico_bytes"],
            "tout": c["timeout"],
            "cod": c["codigo_salida"],
        })

    # Registrar Tiempos y Memoria en medicion_metrica
    await execute_dml("""
        INSERT INTO medicion_metrica (
            ejecucion_id, dimension, indicador, metrica, alcance, valor_numerico, unidad, estado_medicion
        ) VALUES (
            :id, 'eficiencia_desempeno', 'tiempo_ejecucion', 'tiempo_promedio_ms', 'proceso',
            :val, 'ms', :estado
        )
    """, {
        "id": ejecucion_id,
        "val": bench_res["tiempo_promedio_ms"],
        "estado": "valida" if bench_res["tiempo_promedio_ms"] is not None else "error"
    })

    await execute_dml("""
        INSERT INTO medicion_metrica (
            ejecucion_id, dimension, indicador, metrica, alcance, valor_numerico, unidad, estado_medicion
        ) VALUES (
            :id, 'eficiencia_desempeno', 'memoria_pico', 'memoria_mediana_bytes', 'proceso',
            :val, 'bytes', :estado
        )
    """, {
        "id": ejecucion_id,
        "val": bench_res["memoria_mediana_bytes"],
        "estado": "valida" if bench_res["memoria_mediana_bytes"] is not None else "error"
    })

    # 10. Actualizar registro principal de la ejecución
    update_exec_sql = """
        UPDATE ejecucion_experimental
        SET 
            estado_ejecucion = 'completada',
            fecha_fin = now(),
            duracion_generacion_ms = :duracion,
            respuesta_completa = :resp,
            codigo_generado = :cod,
            hash_codigo_sha256 = :sha,
            codigo_parseable = :parseable,
            generacion_exitosa = TRUE,
            estado_validacion = 'valido',
            metadatos = CAST(:meta AS jsonb)
        WHERE ejecucion_id = :id;
    """
    await execute_dml(update_exec_sql, {
        "id": ejecucion_id,
        "duracion": duracion_ms,
        "resp": respuesta_completa,
        "cod": codigo_limpio,
        "sha": hash_sha256,
        "parseable": es_parseable,
        "meta": json.dumps({"modo_inferencia": llm_result.get("modo", "oficial"), "modelo": llm_result.get("modelo")})
    })

    # 11. Auditoría en registro_evento
    await execute_dml("""
        INSERT INTO registro_evento (
            ejecucion_id, nivel, componente, evento, mensaje, datos
        ) VALUES (
            :id, 'INFO', 'Orchestrator', 'EJECUCION_COMPLETADA',
            'Ejecución experimental procesada y evaluada con éxito.',
            CAST(:datos AS jsonb)
        )
    """, {
        "id": ejecucion_id,
        "datos": json.dumps({
            "sha256": hash_sha256,
            "porcentaje_pruebas": pytest_res["porcentaje_aprobadas"],
            "mi": radon_res["maintainability_index"]
        })
    })

    # Mapear respuesta
    return ExecutionResponse(
        ejecucion_id=ejecucion_id,
        problema_id=prob["problema_id"],
        problema_titulo=prob["titulo"],
        tecnica_codigo=tec["codigo"],
        tecnica_nombre=tec["nombre"],
        numero_repeticion=req.numero_repeticion,
        estado_ejecucion="completada",
        estado_validacion="valido",
        duracion_generacion_ms=duracion_ms,
        hash_codigo_sha256=hash_sha256,
        codigo_parseable=es_parseable,
        generacion_exitosa=True,
        prompt_enviado=prompt_text,
        respuesta_completa=respuesta_completa,
        codigo_generado=codigo_limpio,
        porcentaje_pruebas_aprobadas=pytest_res["porcentaje_aprobadas"],
        pruebas_totales=pytest_res["pruebas_totales"],
        pruebas_aprobadas=pytest_res["pruebas_aprobadas"],
        maintainability_index=radon_res["maintainability_index"],
        complejidad_ciclomatica_max=radon_res["complejidad_ciclomatica_max"],
        sloc=radon_res["sloc"],
        tiempo_promedio_ms=bench_res["tiempo_promedio_ms"],
        tiempo_mediano_ms=bench_res["tiempo_mediano_ms"],
        memoria_mediana_kb=bench_res["memoria_mediana_kb"],
        pruebas_detalle=[ResultadoPruebaItem(**p) for p in pytest_res["resultados_detalle"]],
        complejidad_detalle=[ComplejidadItem(**f) for f in radon_res["funciones"]],
        benchmark_detalle=[BenchmarkItem(**c) for c in bench_res["corridas"]]
    )

@router.get("/ejecuciones")
async def list_ejecuciones(
    problema_id: Optional[int] = Query(None),
    tecnica_codigo: Optional[str] = Query(None),
    limit: int = Query(50, le=200)
):
    """Lista las últimas ejecuciones registradas con sus metadatos principales."""
    where_clauses = []
    params = {"limit": limit}

    if problema_id:
        where_clauses.append("e.problema_id = :problema_id")
        params["problema_id"] = problema_id
    if tecnica_codigo:
        where_clauses.append("t.codigo = :tecnica_codigo")
        params["tecnica_codigo"] = tecnica_codigo.upper()

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    query = f"""
        SELECT 
            e.ejecucion_id,
            e.problema_id,
            p.codigo AS problema_codigo,
            p.titulo AS problema_titulo,
            p.dificultad,
            e.tecnica_id,
            t.codigo AS tecnica_codigo,
            t.nombre AS tecnica_nombre,
            e.numero_repeticion,
            e.estado_ejecucion,
            e.duracion_generacion_ms,
            e.hash_codigo_sha256,
            e.creado_en
        FROM ejecucion_experimental e
        JOIN problema p ON p.problema_id = e.problema_id
        JOIN tecnica_prompt t ON t.tecnica_id = e.tecnica_id
        {where_sql}
        ORDER BY e.ejecucion_id DESC
        LIMIT :limit;
    """
    return await fetch_all(query, params)

@router.get("/ejecuciones/{ejecucion_id}")
async def get_ejecucion_detail(ejecucion_id: int):
    """Obtiene el detalle completo de una corrida específica, incluyendo código y resultados."""
    query = """
        SELECT 
            e.ejecucion_id,
            e.problema_id,
            p.codigo AS problema_codigo,
            p.titulo AS problema_titulo,
            p.dificultad,
            e.tecnica_id,
            t.codigo AS tecnica_codigo,
            t.nombre AS tecnica_nombre,
            e.numero_repeticion,
            e.estado_ejecucion,
            e.estado_validacion,
            e.duracion_generacion_ms,
            e.hash_codigo_sha256,
            e.codigo_parseable,
            e.prompt_enviado,
            e.respuesta_completa,
            e.codigo_generado,
            e.creado_en
        FROM ejecucion_experimental e
        JOIN problema p ON p.problema_id = e.problema_id
        JOIN tecnica_prompt t ON t.tecnica_id = e.tecnica_id
        WHERE e.ejecucion_id = :id;
    """
    row = await fetch_one(query, {"id": ejecucion_id})
    if not row:
        raise HTTPException(status_code=404, detail="Ejecución no encontrada")

    # Obtener pruebas
    pruebas = await fetch_all("""
        SELECT identificador_prueba, tipo_prueba, estado, duracion_ms, mensaje_error
        FROM resultado_prueba WHERE ejecucion_id = :id ORDER BY resultado_prueba_id ASC;
    """, {"id": ejecucion_id})

    # Obtener funciones
    funciones = await fetch_all("""
        SELECT nombre_funcion, nombre_clase, linea_inicio, linea_fin, complejidad_ciclomatica
        FROM complejidad_funcion WHERE ejecucion_id = :id;
    """, {"id": ejecucion_id})

    # Obtener benchmark
    benchmark = await fetch_all("""
        SELECT numero_corrida, tipo_corrida, conjunto_entrada, tiempo_ejecucion_ms, memoria_pico_bytes, timeout
        FROM benchmark_corrida WHERE ejecucion_id = :id ORDER BY benchmark_id ASC;
    """, {"id": ejecucion_id})

    row["pruebas_detalle"] = pruebas
    row["complejidad_detalle"] = funciones
    row["benchmark_detalle"] = benchmark
    return row
