"""Executes model-generated Python in a filesystem- and network-isolated process."""
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
from typing import Any, Dict


_WORKER = r"""
import json
import statistics
import sys
import time
import tracemalloc
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO

payload = json.load(sys.stdin)
scope = {"__name__": "__main__", "sys": sys}
result = {"functional": [], "benchmark": None}
sink = StringIO()
try:
    with redirect_stdout(sink), redirect_stderr(sink):
        exec(compile(payload["code"], "<codigo_generado>", "exec"), scope)
except BaseException as exc:
    result["initialization_error"] = f"{type(exc).__name__}: {exc}"
else:
    for test in payload["tests"]:
        started = time.perf_counter()
        try:
            with redirect_stdout(sink), redirect_stderr(sink):
                exec(test["codigo"], scope.copy())
            result["functional"].append({
                "nombre": test["nombre"],
                "estado": "aprobada",
                "duracion_ms": round((time.perf_counter() - started) * 1000, 3),
                "mensaje_error": None,
                "traceback": None,
            })
        except AssertionError as exc:
            result["functional"].append({
                "nombre": test["nombre"],
                "estado": "fallida",
                "duracion_ms": round((time.perf_counter() - started) * 1000, 3),
                "mensaje_error": f"AssertionError: {exc}",
                "traceback": None,
            })
        except BaseException as exc:
            result["functional"].append({
                "nombre": test["nombre"],
                "estado": "error",
                "duracion_ms": round((time.perf_counter() - started) * 1000, 3),
                "mensaje_error": f"{type(exc).__name__}: {exc}",
                "traceback": None,
            })

    warmups = payload["warmup_runs"]
    measurements = payload["measure_runs"]
    if payload["tests"] and (warmups or measurements):
        test = payload["tests"][0]
        runs = []
        times = []
        memories = []
        for number in range(1, warmups + measurements + 1):
            measured = number > warmups
            if measured:
                tracemalloc.start()
            started = time.perf_counter()
            correct = True
            try:
                with redirect_stdout(sink), redirect_stderr(sink):
                    exec(test["codigo"], scope.copy())
            except BaseException:
                correct = False
            elapsed = round((time.perf_counter() - started) * 1000, 6)
            peak = None
            if measured:
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                if correct:
                    times.append(elapsed)
                    memories.append(peak)
            runs.append({
                "numero_corrida": number if not measured else number - warmups,
                "tipo_corrida": "medicion" if measured else "calentamiento",
                "conjunto_entrada": test["nombre"],
                "resultado_correcto": correct,
                "tiempo_ejecucion_ms": elapsed,
                "memoria_pico_bytes": peak,
                "timeout": False,
                "codigo_salida": 0 if correct else 1,
            })
        benchmark = {
            "corridas": runs,
            "tiempo_promedio_ms": round(statistics.mean(times), 6) if times else None,
            "tiempo_mediano_ms": round(statistics.median(times), 6) if times else None,
            "tiempo_minimo_ms": min(times) if times else None,
            "tiempo_maximo_ms": max(times) if times else None,
            "memoria_mediana_bytes": int(statistics.median(memories)) if memories else None,
            "memoria_mediana_kb": round(statistics.median(memories) / 1024, 2) if memories else None,
            "estado_benchmark": "valida" if times else "error",
            "mensaje_error": None if times else "Fallaron todas las corridas de medición.",
        }
        result["benchmark"] = benchmark

print(json.dumps(result))
"""


def _limit_resources() -> None:
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1_048_576, 1_048_576))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_AS, (536_870_912, 536_870_912))


def run_python_sandboxed(
    payload: Dict[str, Any],
    timeout_seconds: float,
) -> Dict[str, Any]:
    """Runs source and test snippets in bubblewrap without network or workspace access."""
    bwrap = shutil.which("bwrap")
    if not bwrap:
        raise RuntimeError("No se encontró bubblewrap (bwrap); se cancela la ejecución no aislada.")

    venv = Path(sys.prefix).resolve()
    command = [
        bwrap,
        "--unshare-net",
        "--unshare-pid",
        "--die-with-parent",
        "--new-session",
        "--ro-bind", "/usr", "/usr",
        "--proc", "/proc",
        "--dev", "/dev",
        "--tmpfs", "/tmp",
        "--chdir", "/tmp",
        "--clearenv",
        "--setenv", "HOME", "/tmp",
        "--setenv", "PATH", "/usr/bin:/bin",
    ]
    for path in (Path("/lib"), Path("/lib64")):
        if path.exists():
            command.extend(["--ro-bind", str(path), str(path)])

    for directory in reversed(venv.parents):
        if str(directory) != "/":
            command.extend(["--dir", str(directory)])
    command.extend(["--ro-bind", str(venv), str(venv)])
    command.extend([
        os.path.realpath(sys.executable),
        "-S",
        "-c",
        _WORKER,
    ])

    try:
        completed = subprocess.run(
            command,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            preexec_fn=_limit_resources,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(f"El proceso aislado superó {timeout_seconds} segundos.") from exc
    if completed.returncode != 0:
        message = completed.stderr.strip() or f"El proceso aislado terminó con código {completed.returncode}."
        raise RuntimeError(f"Falló la ejecución aislada: {message[:1000]}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("El proceso aislado no devolvió un resultado JSON válido.") from exc
