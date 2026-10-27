"""
Evaluador de Exactitud Funcional con Pytest.
Ejecuta los casos de prueba unitarios automatizados contra el código generado por ChatGPT-4o.
"""
import sys
import time
import traceback
from typing import Dict, Any, List

def evaluate_functional_tests(codigo_generado: str, pruebas_funcionales: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ejecuta cada caso de prueba funcional de forma aislada sobre el código generado.
    
    Retorna un diccionario estructurado con:
    - pruebas_totales: int
    - pruebas_aprobadas: int
    - pruebas_fallidas: int
    - pruebas_con_error: int
    - porcentaje_aprobadas: float | None
    - resultados_detalle: List[Dict] (para insertar en resultado_prueba)
    """
    if not pruebas_funcionales:
        return {
            "pruebas_totales": 0,
            "pruebas_aprobadas": 0,
            "pruebas_fallidas": 0,
            "pruebas_con_error": 0,
            "porcentaje_aprobadas": None,
            "resultados_detalle": []
        }

    # Entorno global compartido para la ejecución del código generado
    execution_scope = {
        "__name__": "__main__",
        "sys": sys,
    }

    # Intentar compilar y ejecutar el código generado en el scope
    try:
        compiled_code = compile(codigo_generado, "<codigo_generado>", "exec")
        exec(compiled_code, execution_scope)
    except SyntaxError as syn_err:
        # Si el código no es sintácticamente válido, todas las pruebas se marcan como error
        detalle = []
        for p in pruebas_funcionales:
            nombre = p.get("nombre", "prueba_desconocida")
            detalle.append({
                "identificador_prueba": nombre,
                "tipo_prueba": "funcional",
                "estado": "error",
                "duracion_ms": None,
                "mensaje_error": f"Error de sintaxis en código generado: {str(syn_err)}",
                "traceback": traceback.format_exc(),
            })
        return {
            "pruebas_totales": len(pruebas_funcionales),
            "pruebas_aprobadas": 0,
            "pruebas_fallidas": 0,
            "pruebas_con_error": len(pruebas_funcionales),
            "porcentaje_aprobadas": 0.0,
            "resultados_detalle": detalle,
            "error_compilacion": str(syn_err)
        }
    except Exception as exc:
        detalle = []
        for p in pruebas_funcionales:
            nombre = p.get("nombre", "prueba_desconocida")
            detalle.append({
                "identificador_prueba": nombre,
                "tipo_prueba": "funcional",
                "estado": "error",
                "duracion_ms": None,
                "mensaje_error": f"Error al inicializar código generado: {str(exc)}",
                "traceback": traceback.format_exc(),
            })
        return {
            "pruebas_totales": len(pruebas_funcionales),
            "pruebas_aprobadas": 0,
            "pruebas_fallidas": 0,
            "pruebas_con_error": len(pruebas_funcionales),
            "porcentaje_aprobadas": 0.0,
            "resultados_detalle": detalle,
            "error_inicializacion": str(exc)
        }

    # Ejecutar cada prueba unitaria individualmente
    detalle = []
    aprobadas = 0
    fallidas = 0
    errores = 0

    for prueba in pruebas_funcionales:
        nombre = prueba.get("nombre", f"prueba_{len(detalle) + 1}")
        codigo_prueba = prueba.get("codigo", "")

        test_scope = execution_scope.copy()
        start = time.perf_counter()
        
        try:
            exec(codigo_prueba, test_scope)
            end = time.perf_counter()
            duracion_ms = round((end - start) * 1000.0, 3)
            aprobadas += 1
            detalle.append({
                "identificador_prueba": nombre,
                "tipo_prueba": "funcional",
                "estado": "aprobada",
                "duracion_ms": duracion_ms,
                "mensaje_error": None,
                "traceback": None,
            })
        except AssertionError as assert_err:
            end = time.perf_counter()
            duracion_ms = round((end - start) * 1000.0, 3)
            fallidas += 1
            detalle.append({
                "identificador_prueba": nombre,
                "tipo_prueba": "funcional",
                "estado": "fallida",
                "duracion_ms": duracion_ms,
                "mensaje_error": f"AssertionError: {str(assert_err)}",
                "traceback": traceback.format_exc(),
            })
        except Exception as err:
            end = time.perf_counter()
            duracion_ms = round((end - start) * 1000.0, 3)
            errores += 1
            detalle.append({
                "identificador_prueba": nombre,
                "tipo_prueba": "funcional",
                "estado": "error",
                "duracion_ms": duracion_ms,
                "mensaje_error": f"{type(err).__name__}: {str(err)}",
                "traceback": traceback.format_exc(),
            })

    total = len(pruebas_funcionales)
    pct = round((aprobadas / total) * 100.0, 2) if total > 0 else None

    return {
        "pruebas_totales": total,
        "pruebas_aprobadas": aprobadas,
        "pruebas_fallidas": fallidas,
        "pruebas_con_error": errores,
        "porcentaje_aprobadas": pct,
        "resultados_detalle": detalle
    }
