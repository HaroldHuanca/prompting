"""Functional test runner for generated code in a restricted subprocess."""
from typing import Dict, Any, List

from backend.config import EXECUTION_TIMEOUT_SECONDS
from backend.services.evaluators.python_sandbox import run_python_sandboxed


def evaluate_functional_tests(
    codigo_generado: str,
    pruebas_funcionales: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Runs each test in an isolated, network-disabled Python process."""
    if not pruebas_funcionales:
        return {
            "pruebas_totales": 0,
            "pruebas_aprobadas": 0,
            "pruebas_fallidas": 0,
            "pruebas_con_error": 0,
            "porcentaje_aprobadas": None,
            "resultados_detalle": [],
        }

    tests = [
        {"nombre": test.get("nombre", f"prueba_{i + 1}"), "codigo": test.get("codigo", "")}
        for i, test in enumerate(pruebas_funcionales)
    ]
    try:
        result = run_python_sandboxed(
            {
                "code": codigo_generado,
                "tests": tests,
                "warmup_runs": 0,
                "measure_runs": 0,
            },
            timeout_seconds=EXECUTION_TIMEOUT_SECONDS,
        )
    except TimeoutError as exc:
        details = [
            {
                "identificador_prueba": test["nombre"],
                "tipo_prueba": "funcional",
                "estado": "timeout",
                "duracion_ms": None,
                "mensaje_error": str(exc),
                "traceback": None,
            }
            for test in tests
        ]
        return _summarize(details)
    except RuntimeError as exc:
        details = [
            {
                "identificador_prueba": test["nombre"],
                "tipo_prueba": "funcional",
                "estado": "error",
                "duracion_ms": None,
                "mensaje_error": str(exc),
                "traceback": None,
            }
            for test in tests
        ]
        return _summarize(details)

    initialization_error = result.get("initialization_error")
    if initialization_error:
        details = [
            {
                "identificador_prueba": test["nombre"],
                "tipo_prueba": "funcional",
                "estado": "error",
                "duracion_ms": None,
                "mensaje_error": f"Error al inicializar código generado: {initialization_error}",
                "traceback": None,
            }
            for test in tests
        ]
    else:
        details = [
            {
                **item,
                "identificador_prueba": item["nombre"],
                "tipo_prueba": "funcional",
                "traceback": item.get("traceback"),
            }
            for item in result["functional"]
        ]
    return _summarize(details)


def _summarize(details: List[Dict[str, Any]]) -> Dict[str, Any]:
    passed = sum(item["estado"] == "aprobada" for item in details)
    failed = sum(item["estado"] == "fallida" for item in details)
    errors = len(details) - passed - failed
    total = len(details)
    return {
        "pruebas_totales": total,
        "pruebas_aprobadas": passed,
        "pruebas_fallidas": failed,
        "pruebas_con_error": errors,
        "porcentaje_aprobadas": round(passed / total * 100.0, 2) if total else None,
        "resultados_detalle": details,
    }
