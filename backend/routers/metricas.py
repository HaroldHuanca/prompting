"""
Router de Matriz Comparativa y Consultas Analíticas.
Consulta directamente las vistas relacionales de PostgreSQL:
- vw_resumen_pruebas
- vw_resumen_benchmark
y la tabla medicion_metrica sin imputaciones arbitrarias de 0.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query
from backend.database import fetch_all, fetch_one

router = APIRouter(prefix="/api/metricas", tags=["Métricas y Analítica"])

@router.get("/matriz")
async def get_comparative_matrix(
    problema_id: Optional[int] = Query(None),
    tecnica_codigo: Optional[str] = Query(None),
    dificultad: Optional[str] = Query(None)
):
    """
    Retorna la matriz comparativa consolidada consultando las vistas SQL relacionales
    y las mediciones de Radon y Benchmark.
    """
    where_clauses = ["e.estado_ejecucion = 'completada'"]
    params = {}

    if problema_id:
        where_clauses.append("e.problema_id = :problema_id")
        params["problema_id"] = problema_id
    if tecnica_codigo:
        where_clauses.append("t.codigo = :tecnica_codigo")
        params["tecnica_codigo"] = tecnica_codigo.upper()
    if dificultad:
        where_clauses.append("p.dificultad = :dificultad")
        params["dificultad"] = dificultad

    where_sql = "WHERE " + " AND ".join(where_clauses)

    query = f"""
        SELECT 
            e.ejecucion_id,
            e.problema_id,
            p.codigo AS problema_codigo,
            p.titulo AS problema_titulo,
            p.dificultad,
            p.categoria_algoritmica,
            e.tecnica_id,
            t.codigo AS tecnica_codigo,
            t.nombre AS tecnica_nombre,
            e.numero_repeticion,
            e.duracion_generacion_ms,
            e.hash_codigo_sha256,
            e.creado_en AS fecha_creacion,
            
            -- Desde vista vw_resumen_pruebas
            vp.pruebas_registradas,
            vp.pruebas_aprobadas,
            vp.pruebas_fallidas,
            vp.porcentaje_pruebas_aprobadas,
            
            -- Métricas de Mantenibilidad (Radon)
            m_mi.valor_numerico AS maintainability_index,
            m_cc.valor_numerico::int AS complejidad_ciclomatica_max,
            m_sloc.valor_numerico::int AS sloc,
            
            -- Desde vista vw_resumen_benchmark
            vb.tiempo_promedio_ms,
            vb.tiempo_mediano_ms,
            vb.tiempo_minimo_ms,
            vb.tiempo_maximo_ms,
            vb.memoria_mediana_bytes,
            CASE 
                WHEN vb.memoria_mediana_bytes IS NOT NULL 
                THEN ROUND((vb.memoria_mediana_bytes::numeric / 1024.0), 2)
                ELSE NULL 
            END AS memoria_mediana_kb

        FROM ejecucion_experimental e
        JOIN problema p ON p.problema_id = e.problema_id
        JOIN tecnica_prompt t ON t.tecnica_id = e.tecnica_id
        LEFT JOIN vw_resumen_pruebas vp ON vp.ejecucion_id = e.ejecucion_id
        LEFT JOIN vw_resumen_benchmark vb ON vb.ejecucion_id = e.ejecucion_id
        LEFT JOIN medicion_metrica m_mi ON m_mi.ejecucion_id = e.ejecucion_id AND m_mi.metrica = 'maintainability_index'
        LEFT JOIN medicion_metrica m_cc ON m_cc.ejecucion_id = e.ejecucion_id AND m_cc.metrica = 'complejidad_ciclomatica_max'
        LEFT JOIN medicion_metrica m_sloc ON m_sloc.ejecucion_id = e.ejecucion_id AND m_sloc.metrica = 'sloc'
        {where_sql}
        ORDER BY e.ejecucion_id DESC;
    """
    rows = await fetch_all(query, params)
    return rows

@router.get("/resumen-tecnicas")
async def get_summary_by_technique():
    """
    Agrega las métricas clave por técnica de Prompting (Promedios para gráficos comparativos).
    """
    query = """
        SELECT 
            t.codigo AS tecnica_codigo,
            t.nombre AS tecnica_nombre,
            COUNT(DISTINCT e.ejecucion_id) AS total_ejecuciones,
            ROUND(AVG(vp.porcentaje_pruebas_aprobadas)::numeric, 2) AS promedio_pruebas_aprobadas,
            ROUND(AVG(m_mi.valor_numerico)::numeric, 2) AS promedio_maintainability_index,
            ROUND(AVG(m_cc.valor_numerico)::numeric, 2) AS promedio_complejidad_ciclomatica,
            ROUND(AVG(vb.tiempo_mediano_ms)::numeric, 4) AS promedio_tiempo_mediano_ms,
            ROUND(AVG(vb.memoria_mediana_bytes::numeric / 1024.0)::numeric, 2) AS promedio_memoria_kb
        FROM tecnica_prompt t
        LEFT JOIN ejecucion_experimental e ON e.tecnica_id = t.tecnica_id AND e.estado_ejecucion = 'completada'
        LEFT JOIN vw_resumen_pruebas vp ON vp.ejecucion_id = e.ejecucion_id
        LEFT JOIN vw_resumen_benchmark vb ON vb.ejecucion_id = e.ejecucion_id
        LEFT JOIN medicion_metrica m_mi ON m_mi.ejecucion_id = e.ejecucion_id AND m_mi.metrica = 'maintainability_index'
        LEFT JOIN medicion_metrica m_cc ON m_cc.ejecucion_id = e.ejecucion_id AND m_cc.metrica = 'complejidad_ciclomatica_max'
        WHERE t.activa = TRUE
        GROUP BY t.codigo, t.nombre
        ORDER BY t.codigo;
    """
    return await fetch_all(query)

@router.get("/determinismo")
async def get_determinism_audit():
    """
    Audita la reproducibilidad y determinismo de ChatGPT-4o con T=0.0:
    Agrupa por problema y técnica, evaluando si el hash SHA-256 es idéntico entre repeticiones.
    """
    query = """
        SELECT 
            p.codigo AS problema_codigo,
            p.titulo AS problema_titulo,
            t.codigo AS tecnica_codigo,
            COUNT(e.ejecucion_id) AS total_repeticiones,
            COUNT(DISTINCT e.hash_codigo_sha256) AS hashes_distintos,
            CASE 
                WHEN COUNT(DISTINCT e.hash_codigo_sha256) = 1 AND COUNT(e.ejecucion_id) > 1 THEN 'Determinismo Verificado (100% Idéntico)'
                WHEN COUNT(e.ejecucion_id) <= 1 THEN 'Muestra Única'
                ELSE 'Variabilidad Detectada'
            END AS estado_determinismo
        FROM ejecucion_experimental e
        JOIN problema p ON p.problema_id = e.problema_id
        JOIN tecnica_prompt t ON t.tecnica_id = e.tecnica_id
        WHERE e.estado_ejecucion = 'completada'
        GROUP BY p.codigo, p.titulo, t.codigo
        HAVING COUNT(e.ejecucion_id) >= 1
        ORDER BY p.codigo, t.codigo;
    """
    return await fetch_all(query)
