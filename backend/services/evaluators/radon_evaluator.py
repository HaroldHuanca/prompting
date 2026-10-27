"""
Evaluador de Mantenibilidad y Análisis Estático con Radon.
Calcula Maintainability Index (MI), Complejidad Ciclomática (CC) por función/módulo y SLOC/LOC.
"""
from typing import Dict, Any, List, Optional
from radon.metrics import mi_visit
from radon.complexity import cc_visit
from radon.raw import analyze

def evaluate_code_maintainability(codigo_generado: str) -> Dict[str, Any]:
    """
    Ejecuta el análisis estático con Radon sobre el código generado.
    
    Retorna un diccionario con:
    - maintainability_index: float | None (Escala 0 - 100)
    - complejidad_ciclomatica_max: int | None
    - complejidad_ciclomatica_promedio: float | None
    - loc: int | None
    - sloc: int | None
    - comentarios: int | None
    - funciones: List[Dict] (para insertar en complejidad_funcion)
    - estado_analisis: str ('valida', 'error')
    - mensaje_error: Optional[str]
    """
    if not codigo_generado or not codigo_generado.strip():
        return {
            "maintainability_index": None,
            "complejidad_ciclomatica_max": None,
            "complejidad_ciclomatica_promedio": None,
            "loc": None,
            "sloc": None,
            "comentarios": None,
            "funciones": [],
            "estado_analisis": "error",
            "mensaje_error": "Código vacío o inexistente."
        }

    try:
        # 1. Maintainability Index (MI)
        # multi=False usa la fórmula clásica sin ponderación multi-métrica no estándar
        mi_score = round(float(mi_visit(codigo_generado, multi=False)), 2)

        # 2. Complejidad Ciclomática (CC)
        blocks = cc_visit(codigo_generado)
        funciones_detalle: List[Dict[str, Any]] = []
        complexities: List[int] = []

        for b in blocks:
            # Identificar funciones y métodos
            # b.name, b.complexity, b.lineno, b.endline, getattr(b, 'classname', None)
            es_funcion = getattr(b, 'letter', 'F') in ('F', 'M') or hasattr(b, 'classname')
            c_val = int(b.complexity)
            complexities.append(c_val)

            funciones_detalle.append({
                "nombre_funcion": b.name,
                "nombre_clase": getattr(b, "classname", None),
                "linea_inicio": b.lineno,
                "linea_fin": b.endline,
                "complejidad_ciclomatica": c_val,
                "complejidad_cognitiva": None, # Radon estándar mide ciclomática
            })

        max_cc = max(complexities) if complexities else 1
        avg_cc = round(sum(complexities) / len(complexities), 2) if complexities else 1.0

        # 3. Métricas de Tamaño (LOC / SLOC)
        raw = analyze(codigo_generado)
        loc = raw.loc
        sloc = raw.sloc
        comentarios = raw.comments

        return {
            "maintainability_index": mi_score,
            "complejidad_ciclomatica_max": max_cc,
            "complejidad_ciclomatica_promedio": avg_cc,
            "loc": loc,
            "sloc": sloc,
            "comentarios": comentarios,
            "funciones": funciones_detalle,
            "estado_analisis": "valida",
            "mensaje_error": None
        }

    except SyntaxError as e:
        return {
            "maintainability_index": None,
            "complejidad_ciclomatica_max": None,
            "complejidad_ciclomatica_promedio": None,
            "loc": None,
            "sloc": None,
            "comentarios": None,
            "funciones": [],
            "estado_analisis": "error",
            "mensaje_error": f"Error de sintaxis al analizar con Radon: {str(e)}"
        }
    except Exception as e:
        return {
            "maintainability_index": None,
            "complejidad_ciclomatica_max": None,
            "complejidad_ciclomatica_promedio": None,
            "loc": None,
            "sloc": None,
            "comentarios": None,
            "funciones": [],
            "estado_analisis": "error",
            "mensaje_error": f"Excepción en análisis Radon: {str(e)}"
        }
