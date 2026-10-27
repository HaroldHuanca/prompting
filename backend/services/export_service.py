"""
Servicio de exportación de datos de la plataforma experimental.
Genera datasets científicos en formatos CSV y JSON listos para análisis estadístico (R, Pandas, SPSS).
"""
import csv
import io
import json
from typing import List, Dict, Any

def export_matrix_to_csv(data_rows: List[Dict[str, Any]]) -> str:
    """
    Convierte la matriz de resultados consolidados en una cadena CSV compatible con UTF-8.
    """
    if not data_rows:
        return "ejecucion_id,problema_codigo,titulo,dificultad,categoria,tecnica_codigo,numero_repeticion,porcentaje_pruebas_aprobadas,maintainability_index,complejidad_max,tiempo_promedio_ms,tiempo_mediano_ms,memoria_mediana_kb,duracion_generacion_ms,hash_sha256\n"

    output = io.StringIO()
    # Escribir BOM para soporte nativo en Excel
    output.write('\ufeff')

    headers = [
        "ejecucion_id",
        "problema_codigo",
        "problema_titulo",
        "dificultad",
        "categoria_algoritmica",
        "tecnica_codigo",
        "tecnica_nombre",
        "numero_repeticion",
        "porcentaje_pruebas_aprobadas",
        "pruebas_registradas",
        "pruebas_aprobadas",
        "pruebas_fallidas",
        "maintainability_index",
        "complejidad_ciclomatica_max",
        "sloc",
        "tiempo_promedio_ms",
        "tiempo_mediano_ms",
        "tiempo_minimo_ms",
        "tiempo_maximo_ms",
        "memoria_mediana_kb",
        "duracion_generacion_ms",
        "hash_codigo_sha256",
        "fecha_creacion"
    ]

    writer = csv.DictWriter(output, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()

    for row in data_rows:
        # Formatear valores numéricos o NULL (vacío)
        cleaned_row = {}
        for h in headers:
            val = row.get(h)
            if val is None:
                cleaned_row[h] = ""
            elif isinstance(val, float):
                cleaned_row[h] = round(val, 4)
            else:
                cleaned_row[h] = val
        writer.writerow(cleaned_row)

    return output.getvalue()

def export_matrix_to_json(data_rows: List[Dict[str, Any]]) -> str:
    """
    Exporta la matriz de resultados como JSON estructurado con metadatos del protocolo.
    """
    payload = {
        "metadata": {
            "plataforma": "Prompt Engineering Research Lab",
            "tesis": "Técnicas de Estructuración de Prompts en la Calidad de Código ChatGPT-4o",
            "total_registros": len(data_rows),
            "formato": "ISO-8601 / IEEE 754"
        },
        "registros": data_rows
    }
    return json.dumps(payload, indent=2, ensure_ascii=False, default=str)
