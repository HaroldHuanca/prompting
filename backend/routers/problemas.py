"""
Router de Gestión e Ingesta de Problemas (LeetCode).
Garantiza la segregación estricta entre:
- ejemplos_enunciado (oficiales)
- ejemplos_few_shot (demostraciones para el prompt)
- pruebas_funcionales (casos Pytest)
"""
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.database import fetch_all, fetch_one, execute_dml
from backend.schemas import ProblemaCreate, ProblemaUpdate, ProblemaResponse

router = APIRouter(prefix="/api/problemas", tags=["Problemas"])

@router.get("", response_model=List[ProblemaResponse])
async def list_problemas(
    dificultad: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    solo_activos: bool = Query(True)
):
    """Lista todos los problemas registrados en la plataforma."""
    where_clauses = []
    params = {}

    if solo_activos:
        where_clauses.append("activo = TRUE")
    if dificultad:
        where_clauses.append("dificultad = :dificultad")
        params["dificultad"] = dificultad
    if categoria:
        where_clauses.append("categoria_algoritmica ILIKE :categoria")
        params["categoria"] = f"%{categoria}%"

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    query = f"""
        SELECT 
            problema_id, codigo, titulo, plataforma_origen, url_referencia,
            dificultad, categoria_algoritmica, enunciado, especificacion_entrada,
            especificacion_salida, restricciones, ejemplos_enunciado,
            ejemplos_few_shot, cantidad_ejemplos_few_shot, solucion_referencia,
            pruebas_funcionales, etiquetas, metadatos, version_problema,
            activo, creado_en, actualizado_en
        FROM problema
        {where_sql}
        ORDER BY problema_id ASC;
    """
    rows = await fetch_all(query, params)
    return rows

@router.get("/{problema_id}", response_model=ProblemaResponse)
async def get_problema(problema_id: int):
    """Obtiene el detalle completo de un problema por su ID."""
    query = """
        SELECT 
            problema_id, codigo, titulo, plataforma_origen, url_referencia,
            dificultad, categoria_algoritmica, enunciado, especificacion_entrada,
            especificacion_salida, restricciones, ejemplos_enunciado,
            ejemplos_few_shot, cantidad_ejemplos_few_shot, solucion_referencia,
            pruebas_funcionales, etiquetas, metadatos, version_problema,
            activo, creado_en, actualizado_en
        FROM problema
        WHERE problema_id = :problema_id;
    """
    row = await fetch_one(query, {"problema_id": problema_id})
    if not row:
        raise HTTPException(status_code=404, detail="Problema no encontrado")
    return row

@router.post("", response_model=ProblemaResponse, status_code=201)
async def create_problema(problema: ProblemaCreate):
    """Registra un nuevo problema algorítmico asegurando la segregación de ejemplos y pruebas."""
    # Verificar si el código ya existe
    existente = await fetch_one("SELECT problema_id FROM problema WHERE codigo = :codigo", {"codigo": problema.codigo})
    if existente:
        raise HTTPException(status_code=400, detail=f"Ya existe un problema con el código {problema.codigo}")

    cantidad_few_shot = len(problema.ejemplos_few_shot)

    insert_query = """
        INSERT INTO problema (
            codigo, titulo, plataforma_origen, url_referencia, dificultad,
            categoria_algoritmica, enunciado, especificacion_entrada, especificacion_salida,
            restricciones, ejemplos_enunciado, ejemplos_few_shot, cantidad_ejemplos_few_shot,
            solucion_referencia, pruebas_funcionales, etiquetas
        ) VALUES (
            :codigo, :titulo, :plataforma_origen, :url_referencia, :dificultad,
            :categoria_algoritmica, :enunciado, :especificacion_entrada, :especificacion_salida,
            :restricciones, CAST(:ejemplos_enunciado AS jsonb), CAST(:ejemplos_few_shot AS jsonb), :cantidad_few_shot,
            :solucion_referencia, CAST(:pruebas_funcionales AS jsonb), :etiquetas
        )
        RETURNING problema_id;
    """
    params = {
        "codigo": problema.codigo,
        "titulo": problema.titulo,
        "plataforma_origen": problema.plataforma_origen,
        "url_referencia": problema.url_referencia,
        "dificultad": problema.dificultad,
        "categoria_algoritmica": problema.categoria_algoritmica,
        "enunciado": problema.enunciado,
        "especificacion_entrada": problema.especificacion_entrada,
        "especificacion_salida": problema.especificacion_salida,
        "restricciones": problema.restricciones,
        "ejemplos_enunciado": json.dumps(problema.ejemplos_enunciado),
        "ejemplos_few_shot": json.dumps(problema.ejemplos_few_shot),
        "cantidad_few_shot": cantidad_few_shot,
        "solucion_referencia": problema.solucion_referencia,
        "pruebas_funcionales": json.dumps(problema.pruebas_funcionales),
        "etiquetas": problema.etiquetas,
    }

    created = await fetch_one(insert_query, params)
    return await get_problema(created["problema_id"])

@router.put("/{problema_id}", response_model=ProblemaResponse)
async def update_problema(problema_id: int, problema_update: ProblemaUpdate):
    """Actualiza los campos de un problema existente."""
    actual = await fetch_one("SELECT problema_id FROM problema WHERE problema_id = :id", {"id": problema_id})
    if not actual:
        raise HTTPException(status_code=404, detail="Problema no encontrado")

    set_clauses = ["actualizado_en = now()"]
    params = {"problema_id": problema_id}

    for field, val in problema_update.model_dump(exclude_unset=True).items():
        if field in ("ejemplos_enunciado", "ejemplos_few_shot", "pruebas_funcionales"):
            set_clauses.append(f"{field} = CAST(:{field} AS jsonb)")
            params[field] = json.dumps(val)
            if field == "ejemplos_few_shot":
                set_clauses.append("cantidad_ejemplos_few_shot = :cantidad_fs")
                params["cantidad_fs"] = len(val)
        else:
            set_clauses.append(f"{field} = :{field}")
            params[field] = val

    update_query = f"""
        UPDATE problema
        SET {", ".join(set_clauses)}
        WHERE problema_id = :problema_id;
    """
    await execute_dml(update_query, params)
    return await get_problema(problema_id)

@router.delete("/{problema_id}")
async def delete_problema(problema_id: int):
    """Desactiva un problema lógicamente."""
    actual = await fetch_one("SELECT problema_id FROM problema WHERE problema_id = :id", {"id": problema_id})
    if not actual:
        raise HTTPException(status_code=404, detail="Problema no encontrado")

    await execute_dml(
        "UPDATE problema SET activo = FALSE, actualizado_en = now() WHERE problema_id = :id",
        {"id": problema_id}
    )
    return {"mensaje": f"Problema {problema_id} desactivado correctamente"}

@router.post("/importar-json", response_model=List[ProblemaResponse])
async def import_problemas_json(payload: List[ProblemaCreate] | ProblemaCreate):
    """
    Importa uno o varios problemas a partir de una estructura JSON.
    Si ya existe un problema con el mismo código, lo actualiza (UPSERT).
    """
    items = [payload] if isinstance(payload, ProblemaCreate) else payload
    results = []
    for problema in items:
        existente = await fetch_one("SELECT problema_id FROM problema WHERE codigo = :codigo", {"codigo": problema.codigo})
        cantidad_few_shot = len(problema.ejemplos_few_shot)
        if existente:
            update_query = """
                UPDATE problema SET
                    titulo = :titulo,
                    plataforma_origen = :plataforma_origen,
                    url_referencia = :url_referencia,
                    dificultad = :dificultad,
                    categoria_algoritmica = :categoria_algoritmica,
                    enunciado = :enunciado,
                    especificacion_entrada = :especificacion_entrada,
                    especificacion_salida = :especificacion_salida,
                    restricciones = :restricciones,
                    ejemplos_enunciado = CAST(:ejemplos_enunciado AS jsonb),
                    ejemplos_few_shot = CAST(:ejemplos_few_shot AS jsonb),
                    cantidad_ejemplos_few_shot = :cantidad_few_shot,
                    solucion_referencia = :solucion_referencia,
                    pruebas_funcionales = CAST(:pruebas_funcionales AS jsonb),
                    etiquetas = :etiquetas,
                    activo = TRUE,
                    actualizado_en = now()
                WHERE problema_id = :id;
            """
            params = {
                "id": existente["problema_id"],
                "titulo": problema.titulo,
                "plataforma_origen": problema.plataforma_origen,
                "url_referencia": problema.url_referencia,
                "dificultad": problema.dificultad,
                "categoria_algoritmica": problema.categoria_algoritmica,
                "enunciado": problema.enunciado,
                "especificacion_entrada": problema.especificacion_entrada,
                "especificacion_salida": problema.especificacion_salida,
                "restricciones": problema.restricciones,
                "ejemplos_enunciado": json.dumps(problema.ejemplos_enunciado),
                "ejemplos_few_shot": json.dumps(problema.ejemplos_few_shot),
                "cantidad_few_shot": cantidad_few_shot,
                "solucion_referencia": problema.solucion_referencia,
                "pruebas_funcionales": json.dumps(problema.pruebas_funcionales),
                "etiquetas": problema.etiquetas,
            }
            await execute_dml(update_query, params)
            results.append(await get_problema(existente["problema_id"]))
        else:
            insert_query = """
                INSERT INTO problema (
                    codigo, titulo, plataforma_origen, url_referencia, dificultad,
                    categoria_algoritmica, enunciado, especificacion_entrada, especificacion_salida,
                    restricciones, ejemplos_enunciado, ejemplos_few_shot, cantidad_ejemplos_few_shot,
                    solucion_referencia, pruebas_funcionales, etiquetas
                ) VALUES (
                    :codigo, :titulo, :plataforma_origen, :url_referencia, :dificultad,
                    :categoria_algoritmica, :enunciado, :especificacion_entrada, :especificacion_salida,
                    :restricciones, CAST(:ejemplos_enunciado AS jsonb), CAST(:ejemplos_few_shot AS jsonb), :cantidad_few_shot,
                    :solucion_referencia, CAST(:pruebas_funcionales AS jsonb), :etiquetas
                )
                RETURNING problema_id;
            """
            params = {
                "codigo": problema.codigo,
                "titulo": problema.titulo,
                "plataforma_origen": problema.plataforma_origen,
                "url_referencia": problema.url_referencia,
                "dificultad": problema.dificultad,
                "categoria_algoritmica": problema.categoria_algoritmica,
                "enunciado": problema.enunciado,
                "especificacion_entrada": problema.especificacion_entrada,
                "especificacion_salida": problema.especificacion_salida,
                "restricciones": problema.restricciones,
                "ejemplos_enunciado": json.dumps(problema.ejemplos_enunciado),
                "ejemplos_few_shot": json.dumps(problema.ejemplos_few_shot),
                "cantidad_few_shot": cantidad_few_shot,
                "solucion_referencia": problema.solucion_referencia,
                "pruebas_funcionales": json.dumps(problema.pruebas_funcionales),
                "etiquetas": problema.etiquetas,
            }
            created = await fetch_one(insert_query, params)
            results.append(await get_problema(created["problema_id"]))
    return results
