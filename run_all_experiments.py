import asyncio
import time
import sys
from backend.routers.ejecuciones import execute_experiment
from backend.schemas import ExecutionRequest
from backend.database import fetch_all

CONCURRENCY = 6

async def worker(sem, task_info, total_tasks, completed_counter, lock):
    prob_id = task_info['problema_id']
    prob_code = task_info['codigo']
    tec_cod = task_info['tecnica_codigo']
    rep = task_info['repeticion']

    async with sem:
        retries = 3
        backoff = 2.0
        for attempt in range(retries):
            try:
                t0 = time.perf_counter()
                req = ExecutionRequest(problema_id=prob_id, tecnica_codigo=tec_cod, numero_repeticion=rep)
                res = await execute_experiment(req)
                elapsed = time.perf_counter() - t0
                
                async with lock:
                    completed_counter[0] += 1
                    cur = completed_counter[0]
                    passed = res.pruebas_aprobadas
                    total = res.pruebas_totales
                    pct = res.porcentaje_pruebas_aprobadas
                    print(f"[{cur:3d}/{total_tasks}] {prob_code:7s} | {tec_cod:17s} | Rep {rep} | Tests {passed:2d}/{total:2d} ({pct:5.1f}%) | {elapsed:4.2f}s | ExecID #{res.ejecucion_id}", flush=True)
                return True
            except Exception as e:
                err_msg = str(e)
                if "409" in err_msg or "ya existe" in err_msg:
                    # Already completed previously
                    async with lock:
                        completed_counter[0] += 1
                    return True
                if attempt < retries - 1:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                else:
                    async with lock:
                        completed_counter[0] += 1
                        cur = completed_counter[0]
                        print(f"[{cur:3d}/{total_tasks}] ERROR {prob_code} | {tec_cod} | Rep {rep}: {err_msg}", flush=True)
                    return False

async def main():
    print("=== INICIANDO EXPERIMENTACIÓN EN PROMPTLAB (investigacionv3) ===", flush=True)
    
    # 1. Obtener problemas
    problemas = await fetch_all("SELECT problema_id, codigo, titulo FROM problema ORDER BY problema_id;")
    print(f"Problemas registrados: {len(problemas)}", flush=True)
    
    # 2. Obtener técnicas
    tecnicas = await fetch_all("SELECT tecnica_id, codigo, nombre FROM tecnica_prompt WHERE activa = TRUE ORDER BY tecnica_id;")
    print(f"Técnicas activas: {[t['codigo'] for t in tecnicas]}", flush=True)
    
    # 3. Obtener ejecuciones ya completadas
    existing_rows = await fetch_all("SELECT problema_id, tecnica_id, numero_repeticion FROM ejecucion_experimental WHERE estado_ejecucion = 'completada';")
    tec_id_map = {t['codigo']: t['tecnica_id'] for t in tecnicas}
    existing_set = {(r['problema_id'], r['tecnica_id'], r['numero_repeticion']) for r in existing_rows}
    print(f"Ejecuciones ya completadas previamente: {len(existing_set)}", flush=True)
    
    # 4. Generar tareas pendientes (3 repeticiones por cada problema y técnica)
    tasks = []
    for prob in problemas:
        for tec in tecnicas:
            for rep in [1, 2, 3]:
                key = (prob['problema_id'], tec['tecnica_id'], rep)
                if key not in existing_set:
                    tasks.append({
                        'problema_id': prob['problema_id'],
                        'codigo': prob['codigo'],
                        'tecnica_codigo': tec['codigo'],
                        'repeticion': rep
                    })
                
    total_to_run = len(tasks)
    print(f"Total de ejecuciones a realizar: {total_to_run} (de 360 totales)", flush=True)
    
    if total_to_run == 0:
        print("Todas las 360 ejecuciones ya están completadas en la base de datos.", flush=True)
        return

    sem = asyncio.Semaphore(CONCURRENCY)
    completed_counter = [len(existing_set)]
    lock = asyncio.Lock()
    
    t_start = time.perf_counter()
    results = await asyncio.gather(*[worker(sem, t, 360, completed_counter, lock) for t in tasks])
    t_total = time.perf_counter() - t_start
    
    print("\n" + "="*70, flush=True)
    print(f"EXPERIMENTO COMPLETADO EN {t_total:.1f} segundos ({t_total/60:.2f} minutos)", flush=True)
    print(f"Ejecuciones exitosas: {sum(1 for r in results if r)}/{total_to_run}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())

