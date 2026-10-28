"""Benchmark evaluator for generated code in a restricted subprocess."""
from typing import Dict, Any, List

from backend.config import (
    BENCHMARK_MEASURE_RUNS,
    BENCHMARK_WARMUP_RUNS,
    EXECUTION_TIMEOUT_SECONDS,
)
from backend.services.evaluators.python_sandbox import run_python_sandboxed


def evaluate_benchmark(
    codigo_generado: str,
    pruebas_funcionales: List[Dict[str, Any]],
    warmup_runs: int = BENCHMARK_WARMUP_RUNS,
    measure_runs: int = BENCHMARK_MEASURE_RUNS,
) -> Dict[str, Any]:
    """Measures the first configured test with warmup, timing, and memory samples."""
    if not codigo_generado or not codigo_generado.strip() or not pruebas_funcionales:
        return _error("Código o pruebas no disponibles para benchmark.")

    tests = [
        {"nombre": test.get("nombre", f"prueba_{i + 1}"), "codigo": test.get("codigo", "")}
        for i, test in enumerate(pruebas_funcionales[:1])
    ]
    timeout_seconds = max(
        EXECUTION_TIMEOUT_SECONDS,
        min(30.0, (warmup_runs + measure_runs) * EXECUTION_TIMEOUT_SECONDS),
    )
    try:
        result = run_python_sandboxed(
            {
                "code": codigo_generado,
                "tests": tests,
                "warmup_runs": warmup_runs,
                "measure_runs": measure_runs,
            },
            timeout_seconds=timeout_seconds,
        )
    except (RuntimeError, TimeoutError) as exc:
        return _error(str(exc))

    if result.get("initialization_error"):
        return _error(f"Error de inicialización en benchmark: {result['initialization_error']}")
    benchmark = result.get("benchmark")
    return benchmark if benchmark is not None else _error("No se pudieron recopilar mediciones.")


def _error(message: str) -> Dict[str, Any]:
    return {
        "corridas": [],
        "tiempo_promedio_ms": None,
        "tiempo_mediano_ms": None,
        "tiempo_minimo_ms": None,
        "tiempo_maximo_ms": None,
        "memoria_mediana_bytes": None,
        "memoria_mediana_kb": None,
        "estado_benchmark": "error",
        "mensaje_error": message,
    }
