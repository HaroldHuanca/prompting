"""
Evaluador de Desempeño y Perfilamiento de Eficiencia.
Mide tiempo de ejecución con timeit (calentamiento + repeticiones) y memoria pico con tracemalloc.
"""
import statistics
import time
import tracemalloc
from typing import Dict, Any, List, Optional
from backend.config import BENCHMARK_WARMUP_RUNS, BENCHMARK_MEASURE_RUNS

def evaluate_benchmark(
    codigo_generado: str, 
    pruebas_funcionales: List[Dict[str, Any]],
    warmup_runs: int = BENCHMARK_WARMUP_RUNS,
    measure_runs: int = BENCHMARK_MEASURE_RUNS
) -> Dict[str, Any]:
    """
    Ejecuta el protocolo de benchmarking:
    1. Fase de calentamiento (warm-up) para estabilización de caché y JIT/C-Python.
    2. Fase de medición cronometrada repetida.
    3. Medición de memoria pico con tracemalloc.
    """
    if not codigo_generado or not codigo_generado.strip() or not pruebas_funcionales:
        return {
            "corridas": [],
            "tiempo_promedio_ms": None,
            "tiempo_mediano_ms": None,
            "tiempo_minimo_ms": None,
            "tiempo_maximo_ms": None,
            "memoria_mediana_bytes": None,
            "memoria_mediana_kb": None,
            "estado_benchmark": "error",
            "mensaje_error": "Código o pruebas no disponibles para benchmark."
        }

    # Compilar el código generado
    scope = {"__name__": "__main__"}
    try:
        compiled = compile(codigo_generado, "<benchmark_target>", "exec")
        exec(compiled, scope)
    except Exception as e:
        return {
            "corridas": [],
            "tiempo_promedio_ms": None,
            "tiempo_mediano_ms": None,
            "tiempo_minimo_ms": None,
            "tiempo_maximo_ms": None,
            "memoria_mediana_bytes": None,
            "memoria_mediana_kb": None,
            "estado_benchmark": "error",
            "mensaje_error": f"Error de inicialización en benchmark: {str(e)}"
        }

    # Seleccionar caso de benchmark representativo (el primer caso de prueba)
    test_repr = pruebas_funcionales[0].get("codigo", "")
    conjunto_entrada = pruebas_funcionales[0].get("nombre", "caso_base")

    corridas_detalle: List[Dict[str, Any]] = []

    # 1. Fase de Calentamiento (Warm-up)
    for w in range(1, warmup_runs + 1):
        test_scope = scope.copy()
        t0 = time.perf_counter()
        timeout = False
        correcto = True
        try:
            exec(test_repr, test_scope)
        except Exception:
            correcto = False
        t1 = time.perf_counter()
        tiempo_ms = round((t1 - t0) * 1000.0, 6)

        corridas_detalle.append({
            "numero_corrida": w,
            "tipo_corrida": "calentamiento",
            "conjunto_entrada": conjunto_entrada,
            "resultado_correcto": correcto,
            "tiempo_ejecucion_ms": tiempo_ms,
            "memoria_pico_bytes": None, # tracemalloc activo solo en medición para no ralentizar calentamiento
            "timeout": timeout,
            "codigo_salida": 0 if correcto else 1
        })

    # 2. Fase de Medición (repeticiones controladas)
    tiempos_medicion: List[float] = []
    memorias_medicion: List[int] = []

    for m in range(1, measure_runs + 1):
        test_scope = scope.copy()
        tracemalloc.start()
        t0 = time.perf_counter()
        timeout = False
        correcto = True
        try:
            exec(test_repr, test_scope)
        except Exception:
            correcto = False
        t1 = time.perf_counter()
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        tiempo_ms = round((t1 - t0) * 1000.0, 6)
        if correcto:
            tiempos_medicion.append(tiempo_ms)
            memorias_medicion.append(peak_bytes)

        corridas_detalle.append({
            "numero_corrida": m,
            "tipo_corrida": "medicion",
            "conjunto_entrada": conjunto_entrada,
            "resultado_correcto": correcto,
            "tiempo_ejecucion_ms": tiempo_ms,
            "memoria_pico_bytes": peak_bytes,
            "timeout": timeout,
            "codigo_salida": 0 if correcto else 1
        })

    # Calcular estadísticas consolidadas
    if tiempos_medicion:
        tiempo_promedio = round(statistics.mean(tiempos_medicion), 6)
        tiempo_mediano = round(statistics.median(tiempos_medicion), 6)
        tiempo_minimo = round(min(tiempos_medicion), 6)
        tiempo_maximo = round(max(tiempos_medicion), 6)
    else:
        tiempo_promedio = None
        tiempo_mediano = None
        tiempo_minimo = None
        tiempo_maximo = None

    if memorias_medicion:
        memoria_mediana = int(statistics.median(memorias_medicion))
        memoria_mediana_kb = round(memoria_mediana / 1024.0, 2)
    else:
        memoria_mediana = None
        memoria_mediana_kb = None

    return {
        "corridas": corridas_detalle,
        "tiempo_promedio_ms": tiempo_promedio,
        "tiempo_mediano_ms": tiempo_mediano,
        "tiempo_minimo_ms": tiempo_minimo,
        "tiempo_maximo_ms": tiempo_maximo,
        "memoria_mediana_bytes": memoria_mediana,
        "memoria_mediana_kb": memoria_mediana_kb,
        "estado_benchmark": "valida" if tiempos_medicion else "error",
        "mensaje_error": None if tiempos_medicion else "Fallaron todas las corridas de medición."
    }
