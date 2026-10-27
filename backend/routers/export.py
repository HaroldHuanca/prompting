"""
Router de Exportación de Datasets Experimentales.
Provee endpoints de descarga directa en formatos CSV y JSON para R y Pandas.
"""
from typing import Optional
from fastapi import APIRouter, Response, Query
from backend.routers.metricas import get_comparative_matrix
from backend.services.export_service import export_matrix_to_csv, export_matrix_to_json

router = APIRouter(prefix="/api/export", tags=["Exportación"])

@router.get("/csv")
async def export_csv(
    problema_id: Optional[int] = Query(None),
    tecnica_codigo: Optional[str] = Query(None),
    dificultad: Optional[str] = Query(None)
):
    """Descarga la matriz de resultados en formato CSV normalizado."""
    data = await get_comparative_matrix(problema_id, tecnica_codigo, dificultad)
    csv_content = export_matrix_to_csv(data)
    
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=dataset_experimental_prompting.csv"
        }
    )

@router.get("/json")
async def export_json(
    problema_id: Optional[int] = Query(None),
    tecnica_codigo: Optional[str] = Query(None),
    dificultad: Optional[str] = Query(None)
):
    """Descarga la matriz de resultados en formato JSON estructurado con metadatos."""
    data = await get_comparative_matrix(problema_id, tecnica_codigo, dificultad)
    json_content = export_matrix_to_json(data)
    
    return Response(
        content=json_content,
        media_type="application/json; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=dataset_experimental_prompting.json"
        }
    )
