import asyncio
import time
from sqlalchemy import text
from backend.database import AsyncSessionLocal, fetch_all
from backend.services.evaluators.pytest_evaluator import evaluate_functional_tests
from backend.services.evaluators.benchmark_evaluator import evaluate_benchmark
from backend.config import EXECUTION_TIMEOUT_SECONDS

CONCURRENCY = 4

async def update_db_for_execution(exec_id, parseable, pytest_res, bench_res):
    async with AsyncSessionLocal() as session:
        await session.execute(text("SET search_path TO experimento, public;"))

        # 1. Update resultado_prueba
        await session.execute(
            text("DELETE FROM resultado_prueba WHERE ejecucion_id = :id;"),
            {"id": exec_id}
        )

        test_records = []
        for p in pytest_res.get("resultados_detalle", []):
            test_records.append({
                "ejecucion_id": exec_id,
                "identificador_prueba": p["identificador_prueba"],
                "tipo_prueba": p["tipo_prueba"],
                "estado": p["estado"],
                "duracion_ms": p["duracion_ms"],
                "mensaje_error": p["mensaje_error"],
                "traceback": p["traceback"]
            })

        if test_records:
            await session.execute(
                text("""
                    INSERT INTO resultado_prueba (
                        ejecucion_id, identificador_prueba, tipo_prueba, estado, duracion_ms, mensaje_error, traceback
                    ) VALUES (
                        :ejecucion_id, :identificador_prueba, :tipo_prueba, :estado, :duracion_ms, :mensaje_error, :traceback
                    );
                """),
                test_records
            )

        # 2. Update benchmark_corrida
        await session.execute(
            text("DELETE FROM benchmark_corrida WHERE ejecucion_id = :id;"),
            {"id": exec_id}
        )

        bench_records = []
        for c in bench_res.get("corridas", []):
            bench_records.append({
                "ejecucion_id": exec_id,
                "numero_corrida": c["numero_corrida"],
                "tipo_corrida": c["tipo_corrida"],
                "conjunto_entrada": c["conjunto_entrada"],
                "resultado_correcto": c["resultado_correcto"],
                "tiempo_ejecucion_ms": c["tiempo_ejecucion_ms"],
                "memoria_pico_bytes": c["memoria_pico_bytes"],
                "timeout": c["timeout"],
                "codigo_salida": c["codigo_salida"],
            })

        if bench_records:
            await session.execute(
                text("""
                    INSERT INTO benchmark_corrida (
                        ejecucion_id, numero_corrida, tipo_corrida, conjunto_entrada,
                        resultado_correcto, tiempo_ejecucion_ms, memoria_pico_bytes, timeout, codigo_salida
                    ) VALUES (
                        :ejecucion_id, :numero_corrida, :tipo_corrida, :conjunto_entrada,
                        :resultado_correcto, :tiempo_ejecucion_ms, :memoria_pico_bytes, :timeout, :codigo_salida
                    );
                """),
                bench_records
            )

        # 3. Update medicion_metrica
        await session.execute(
            text("""
                DELETE FROM medicion_metrica 
                WHERE ejecucion_id = :id AND metrica IN ('tiempo_promedio_ms', 'memoria_mediana_bytes');
            """),
            {"id": exec_id}
        )

        metric_records = [
            {
                "ejecucion_id": exec_id,
                "dimension": "eficiencia_desempeno",
                "indicador": "tiempo_ejecucion",
                "metrica": "tiempo_promedio_ms",
                "alcance": "proceso",
                "valor_numerico": bench_res.get("tiempo_promedio_ms"),
                "unidad": "ms",
                "estado_medicion": "valida" if bench_res.get("tiempo_promedio_ms") is not None else "error"
            },
            {
                "ejecucion_id": exec_id,
                "dimension": "eficiencia_desempeno",
                "indicador": "memoria_pico",
                "metrica": "memoria_mediana_bytes",
                "alcance": "proceso",
                "valor_numerico": bench_res.get("memoria_mediana_bytes"),
                "unidad": "bytes",
                "estado_medicion": "valida" if bench_res.get("memoria_mediana_bytes") is not None else "error"
            }
        ]

        await session.execute(
            text("""
                INSERT INTO medicion_metrica (
                    ejecucion_id, dimension, indicador, metrica, alcance, valor_numerico, unidad, estado_medicion
                ) VALUES (
                    :ejecucion_id, :dimension, :indicador, :metrica, :alcance, :valor_numerico, :unidad, :estado_medicion
                );
            """),
            metric_records
        )

        # 4. Update ejecucion_experimental
        is_valido = bool(parseable and pytest_res.get("porcentaje_aprobadas") == 100.0)
        await session.execute(
            text("""
                UPDATE ejecucion_experimental
                SET estado_validacion = :valido
                WHERE ejecucion_id = :id;
            """),
            {
                "id": exec_id,
                "valido": "valido" if is_valido else "invalido"
            }
        )

        await session.commit()

async def retest_execution(sem, exec_data, total, counter, lock):
    exec_id = exec_data["ejecucion_id"]
    code = exec_data["codigo_generado"] or ""
    parseable = exec_data["codigo_parseable"]
    tests = exec_data["pruebas_funcionales"] or []

    async with sem:
        t0 = time.perf_counter()
        
        # 1. Functional tests with 25s timeout (run in background executor to not block async loop)
        loop = asyncio.get_running_loop()
        pytest_res = await loop.run_in_executor(None, evaluate_functional_tests, code, tests)
        
        # 2. Benchmark evaluation (only if at least 1 test passed; skip if code times out or fails entirely)
        if pytest_res.get("pruebas_aprobadas", 0) > 0:
            bench_res = await loop.run_in_executor(None, evaluate_benchmark, code, tests)
        else:
            bench_res = {
                "corridas": [],
                "tiempo_promedio_ms": None,
                "tiempo_mediano_ms": None,
                "memoria_mediana_bytes": None
            }
        
        elapsed = time.perf_counter() - t0

        # 3. Update Database in investigacionv4
        retries = 3
        for attempt in range(retries):
            try:
                await update_db_for_execution(exec_id, parseable, pytest_res, bench_res)
                break
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(1.0)
                else:
                    print(f"Error updating DB for exec #{exec_id}: {e}", flush=True)

        async with lock:
            counter[0] += 1
            cur = counter[0]
            if cur % 20 == 0 or cur == total:
                passed = pytest_res["pruebas_aprobadas"]
                tot = pytest_res["pruebas_totales"]
                pct = pytest_res["porcentaje_aprobadas"]
                print(f"[{cur:3d}/{total}] ExecID #{exec_id:3d} | Tests {passed:2d}/{tot:2d} ({pct:5.1f}%) | {elapsed:5.2f}s", flush=True)

async def main():
    print(f"=== RE-EVALUANDO PRUEBAS EN investigacionv4 (TIMEOUT={EXECUTION_TIMEOUT_SECONDS}s) ===", flush=True)
    
    rows = await fetch_all("""
        SELECT 
            e.ejecucion_id,
            e.problema_id,
            e.codigo_generado,
            e.codigo_parseable,
            p.pruebas_funcionales
        FROM ejecucion_experimental e
        JOIN problema p ON p.problema_id = e.problema_id
        ORDER BY e.ejecucion_id ASC;
    """)
    total = len(rows)
    print(f"Total de ejecuciones a reevaluar: {total}", flush=True)

    sem = asyncio.Semaphore(CONCURRENCY)
    counter = [0]
    lock = asyncio.Lock()
    
    t_start = time.perf_counter()
    await asyncio.gather(*[retest_execution(sem, r, total, counter, lock) for r in rows])
    t_total = time.perf_counter() - t_start

    print("\n" + "="*70, flush=True)
    print(f"REEVALUACIÓN COMPLETADA EN {t_total:.1f} segundos ({t_total/60:.2f} minutos)", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
