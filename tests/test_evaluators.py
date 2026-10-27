"""
Pruebas unitarias para los evaluadores automatizados:
1. Pytest (Exactitud funcional)
2. Radon (Mantenibilidad, CC, LOC)
3. Benchmark (timeit + tracemalloc)
"""
import pytest
from backend.services.evaluators.pytest_evaluator import evaluate_functional_tests
from backend.services.evaluators.radon_evaluator import evaluate_code_maintainability
from backend.services.evaluators.benchmark_evaluator import evaluate_benchmark

VALID_CODE = """
class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        seen = {}
        for i, num in enumerate(nums):
            comp = target - num
            if comp in seen:
                return [seen[comp], i]
            seen[num] = i
        return []
"""

FAILING_CODE = """
class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        # Implementación errónea a propósito
        return [0, 0]
"""

SYNTAX_ERROR_CODE = """
class Solution:
    def twoSum(self, nums, target)
        return []
"""

TEST_CASES = [
    {"nombre": "test_1", "codigo": "assert Solution().twoSum([2, 7, 11, 15], 9) in [[0, 1], [1, 0]]"},
    {"nombre": "test_2", "codigo": "assert Solution().twoSum([3, 2, 4], 6) in [[1, 2], [2, 1]]"},
    {"nombre": "test_3", "codigo": "assert Solution().twoSum([3, 3], 6) in [[0, 1], [1, 0]]"}
]

# -----------------------------------------------------------------------------
# 1. PRUEBAS PYTEST EVALUATOR
# -----------------------------------------------------------------------------
def test_pytest_evaluator_all_passed():
    res = evaluate_functional_tests(VALID_CODE, TEST_CASES)
    assert res["pruebas_totales"] == 3
    assert res["pruebas_aprobadas"] == 3
    assert res["pruebas_fallidas"] == 0
    assert res["porcentaje_aprobadas"] == 100.0
    assert len(res["resultados_detalle"]) == 3
    for d in res["resultados_detalle"]:
        assert d["estado"] == "aprobada"
        assert d["duracion_ms"] is not None

def test_pytest_evaluator_assertions_failed():
    res = evaluate_functional_tests(FAILING_CODE, TEST_CASES)
    assert res["pruebas_totales"] == 3
    assert res["pruebas_aprobadas"] == 0
    assert res["pruebas_fallidas"] == 3
    assert res["porcentaje_aprobadas"] == 0.0
    for d in res["resultados_detalle"]:
        assert d["estado"] == "fallida"
        assert "AssertionError" in d["mensaje_error"]

def test_pytest_evaluator_syntax_error():
    res = evaluate_functional_tests(SYNTAX_ERROR_CODE, TEST_CASES)
    assert res["pruebas_totales"] == 3
    assert res["pruebas_con_error"] == 3
    assert res["porcentaje_aprobadas"] == 0.0

# -----------------------------------------------------------------------------
# 2. PRUEBAS RADON EVALUATOR
# -----------------------------------------------------------------------------
def test_radon_evaluator_valid_code():
    res = evaluate_code_maintainability(VALID_CODE)
    assert res["estado_analisis"] == "valida"
    assert res["maintainability_index"] is not None
    assert 0 <= res["maintainability_index"] <= 100
    assert res["complejidad_ciclomatica_max"] >= 1
    assert res["sloc"] is not None
    assert len(res["funciones"]) >= 1

def test_radon_evaluator_syntax_error_returns_none():
    # Regla científica de integridad: NUNCA sustituir por 0, devolver None
    res = evaluate_code_maintainability(SYNTAX_ERROR_CODE)
    assert res["estado_analisis"] == "error"
    assert res["maintainability_index"] is None
    assert res["complejidad_ciclomatica_max"] is None
    assert res["sloc"] is None
    assert res["mensaje_error"] is not None

# -----------------------------------------------------------------------------
# 3. PRUEBAS BENCHMARK EVALUATOR
# -----------------------------------------------------------------------------
def test_benchmark_evaluator_runs():
    res = evaluate_benchmark(VALID_CODE, TEST_CASES, warmup_runs=2, measure_runs=5)
    assert res["estado_benchmark"] == "valida"
    assert len(res["corridas"]) == 7 # 2 warmup + 5 measurement
    assert res["tiempo_promedio_ms"] is not None
    assert res["tiempo_mediano_ms"] is not None
    assert res["memoria_mediana_bytes"] is not None
    assert res["memoria_mediana_kb"] is not None
    assert res["tiempo_minimo_ms"] <= res["tiempo_maximo_ms"]
