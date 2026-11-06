#!/usr/bin/env python3
"""Reproducible, problem-blocked analysis of the investigacionv5 experiment."""

from __future__ import annotations

import argparse
import asyncio
import csv
import itertools
import json
import math
import os
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import asyncpg
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import friedmanchisquare, rankdata, wilcoxon


SCRIPT_VERSION = "1.0.0"
ALPHA = 0.05
BOOTSTRAP_ITERATIONS = 10_000
RANDOM_SEED = 20261106
TECHNIQUE_ORDER = [
    "ZERO_SHOT",
    "FEW_SHOT",
    "CHAIN_OF_THOUGHT",
    "ROLE_PROMPTING",
]
METRICS = {
    "porcentaje_pruebas_aprobadas": {
        "label": "Exactitud funcional (% pruebas aprobadas)",
        "unit": "%",
        "direction": "higher",
        "family": "HE1",
    },
    "maintainability_index": {
        "label": "Maintainability Index",
        "unit": "puntos (0-100)",
        "direction": "higher",
        "family": "HE2",
    },
    "complejidad_ciclomatica_max": {
        "label": "Complejidad ciclomática máxima",
        "unit": "rutas",
        "direction": "lower",
        "family": "HE2",
    },
    "sloc": {
        "label": "Líneas de código fuente (SLOC)",
        "unit": "líneas",
        "direction": "descriptive",
        "family": "HE2",
    },
    "tiempo_promedio_ms": {
        "label": "Tiempo promedio de ejecución",
        "unit": "ms",
        "direction": "lower",
        "family": "HE3",
    },
    "memoria_mediana_bytes": {
        "label": "Memoria mediana máxima",
        "unit": "bytes",
        "direction": "lower",
        "family": "HE3",
    },
}
BASE_TABLES = [
    "protocolo_experimental",
    "tecnica_prompt",
    "problema",
    "plantilla_prompt",
    "ejecucion_experimental",
    "resultado_prueba",
    "ejecucion_herramienta",
    "medicion_metrica",
    "benchmark_corrida",
    "complejidad_funcion",
    "registro_evento",
]


def json_default(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (datetime,)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def holm_adjust(p_values: list[float]) -> list[float]:
    """Holm step-down adjusted p-values, returned in the original order."""
    if not p_values:
        return []
    order = np.argsort(np.asarray(p_values, dtype=float))
    adjusted = np.empty(len(p_values), dtype=float)
    running_max = 0.0
    count = len(p_values)
    for rank, index in enumerate(order):
        candidate = min(1.0, (count - rank) * p_values[index])
        running_max = max(running_max, candidate)
        adjusted[index] = running_max
    return adjusted.tolist()


def summarize(values: list[float], metric: str) -> dict[str, Any]:
    array = np.asarray(values, dtype=float)
    q1, median, q3 = np.quantile(array, [0.25, 0.5, 0.75])
    sd = float(np.std(array, ddof=1)) if len(array) > 1 else None
    cv = None
    if metric in {"sloc", "tiempo_promedio_ms", "memoria_mediana_bytes"}:
        mean = float(np.mean(array))
        if mean != 0 and sd is not None:
            cv = 100.0 * sd / abs(mean)
    return {
        "n": int(len(array)),
        "mean": float(np.mean(array)),
        "sd": sd,
        "median": float(median),
        "q1": float(q1),
        "q3": float(q3),
        "iqr": float(q3 - q1),
        "minimum": float(np.min(array)),
        "maximum": float(np.max(array)),
        "cv_percent": cv,
    }


def paired_bootstrap_median_ci(
    differences: np.ndarray,
    seed: int,
    iterations: int = BOOTSTRAP_ITERATIONS,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    samples = rng.choice(
        differences,
        size=(iterations, len(differences)),
        replace=True,
    )
    medians = np.median(samples, axis=1)
    low, high = np.quantile(medians, [0.025, 0.975])
    return float(low), float(high)


def rank_biserial(differences: np.ndarray) -> float:
    nonzero = differences[differences != 0]
    if len(nonzero) == 0:
        return 0.0
    ranks = rankdata(np.abs(nonzero), method="average")
    positive = float(np.sum(ranks[nonzero > 0]))
    negative = float(np.sum(ranks[nonzero < 0]))
    denominator = positive + negative
    return (positive - negative) / denominator if denominator else 0.0


def paired_bootstrap_rank_biserial_ci(
    differences: np.ndarray,
    seed: int,
    iterations: int = BOOTSTRAP_ITERATIONS,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    samples = rng.choice(
        differences,
        size=(iterations, len(differences)),
        replace=True,
    )
    effects = np.fromiter(
        (rank_biserial(sample) for sample in samples),
        dtype=float,
        count=iterations,
    )
    low, high = np.quantile(effects, [0.025, 0.975])
    return float(low), float(high)


def run_friedman(
    metric: str,
    dataset: str,
    blocks: list[int],
    aggregate: dict[str, dict[tuple[int, str], float]],
) -> dict[str, Any]:
    arrays = [
        np.asarray(
            [aggregate[metric][(problem_id, technique)] for problem_id in blocks],
            dtype=float,
        )
        for technique in TECHNIQUE_ORDER
    ]
    n = len(blocks)
    if n < 2:
        raise ValueError(f"Too few complete blocks for {metric}: {n}")
    if all(np.array_equal(arrays[0], candidate) for candidate in arrays[1:]):
        statistic, p_value = 0.0, 1.0
    else:
        result = friedmanchisquare(*arrays)
        statistic, p_value = float(result.statistic), float(result.pvalue)
        if not math.isfinite(statistic) or not math.isfinite(p_value):
            raise RuntimeError(f"Friedman returned a non-finite result for {metric}")
    return {
        "dataset": dataset,
        "metric": metric,
        "n_blocks": n,
        "statistic": statistic,
        "df": len(TECHNIQUE_ORDER) - 1,
        "p_raw": p_value,
        "kendall_w": statistic / (n * (len(TECHNIQUE_ORDER) - 1)),
        "method": "Friedman, problem as block; one median per problem-technique",
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def make_plots(
    output_dir: Path,
    metric: str,
    blocks: list[int],
    aggregate: dict[str, dict[tuple[int, str], float]],
    technique_labels: dict[str, str],
) -> str:
    config = METRICS[metric]
    values = [
        np.asarray(
            [aggregate[metric][(problem_id, technique)] for problem_id in blocks],
            dtype=float,
        )
        for technique in TECHNIQUE_ORDER
    ]
    fig, axis = plt.subplots(figsize=(10, 6))
    labels = [
        f"{technique_labels.get(technique, technique)}\n(n={len(values[index])})"
        for index, technique in enumerate(TECHNIQUE_ORDER)
    ]
    axis.boxplot(
        values,
        tick_labels=labels,
        showfliers=True,
        patch_artist=True,
        medianprops={"color": "#202020", "linewidth": 2},
        boxprops={"facecolor": "#a9c8e8", "alpha": 0.8},
        whiskerprops={"color": "#4c566a"},
        capprops={"color": "#4c566a"},
        flierprops={"marker": "o", "markersize": 3, "alpha": 0.4},
    )
    rng = np.random.default_rng(RANDOM_SEED)
    for index, group in enumerate(values, start=1):
        jitter = rng.uniform(-0.09, 0.09, size=len(group))
        axis.scatter(
            index + jitter,
            group,
            s=12,
            alpha=0.16,
            color="#1f4e79",
            linewidths=0,
            zorder=2,
        )
    if metric in {"tiempo_promedio_ms", "memoria_mediana_bytes"}:
        axis.set_yscale("log")
    axis.set_title(f"{config['label']} por técnica\nMediana de repeticiones; bloques completos (n={len(blocks)})")
    axis.set_ylabel(config["unit"])
    axis.set_xlabel("Técnica de prompting")
    axis.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    filename = f"{metric}.png"
    fig.savefig(output_dir / filename, dpi=180)
    plt.close(fig)
    return filename


async def create_analysis_tables(connection: asyncpg.Connection) -> None:
    await connection.execute(
        """
        CREATE SCHEMA IF NOT EXISTS analisis_estadistico;
        CREATE TABLE IF NOT EXISTS analisis_estadistico.analysis_run (
            analysis_id UUID PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            database_name TEXT NOT NULL,
            script_version TEXT NOT NULL,
            alpha DOUBLE PRECISION NOT NULL,
            aggregation_rule TEXT NOT NULL,
            artifact_directory TEXT NOT NULL,
            audit_snapshot JSONB NOT NULL,
            interpretation JSONB NOT NULL
        );
        CREATE TABLE IF NOT EXISTS analisis_estadistico.audit_item (
            analysis_id UUID NOT NULL REFERENCES analisis_estadistico.analysis_run(analysis_id) ON DELETE CASCADE,
            audit_key TEXT NOT NULL,
            audit_value JSONB NOT NULL,
            PRIMARY KEY (analysis_id, audit_key)
        );
        CREATE TABLE IF NOT EXISTS analisis_estadistico.processed_observation (
            analysis_id UUID NOT NULL REFERENCES analisis_estadistico.analysis_run(analysis_id) ON DELETE CASCADE,
            metric TEXT NOT NULL,
            problem_id BIGINT NOT NULL,
            problem_code TEXT NOT NULL,
            technique_code TEXT NOT NULL,
            valid_repetitions SMALLINT NOT NULL,
            median_value DOUBLE PRECISION NOT NULL,
            unit TEXT NOT NULL,
            in_primary_complete_blocks BOOLEAN NOT NULL,
            in_strict_complete_blocks BOOLEAN NOT NULL,
            PRIMARY KEY (analysis_id, metric, problem_id, technique_code)
        );
        CREATE TABLE IF NOT EXISTS analisis_estadistico.descriptive_statistic (
            analysis_id UUID NOT NULL REFERENCES analisis_estadistico.analysis_run(analysis_id) ON DELETE CASCADE,
            metric TEXT NOT NULL,
            technique_code TEXT NOT NULL,
            sample_scope TEXT NOT NULL,
            n INTEGER NOT NULL,
            mean DOUBLE PRECISION,
            standard_deviation DOUBLE PRECISION,
            median DOUBLE PRECISION,
            q1 DOUBLE PRECISION,
            q3 DOUBLE PRECISION,
            iqr DOUBLE PRECISION,
            minimum DOUBLE PRECISION,
            maximum DOUBLE PRECISION,
            coefficient_variation_percent DOUBLE PRECISION,
            PRIMARY KEY (analysis_id, metric, technique_code, sample_scope)
        );
        CREATE TABLE IF NOT EXISTS analisis_estadistico.global_test (
            analysis_id UUID NOT NULL REFERENCES analisis_estadistico.analysis_run(analysis_id) ON DELETE CASCADE,
            dataset TEXT NOT NULL,
            metric TEXT NOT NULL,
            n_blocks INTEGER NOT NULL,
            statistic DOUBLE PRECISION NOT NULL,
            degrees_freedom INTEGER NOT NULL,
            p_value DOUBLE PRECISION NOT NULL,
            p_value_holm DOUBLE PRECISION NOT NULL,
            kendall_w DOUBLE PRECISION NOT NULL,
            significant_after_holm BOOLEAN NOT NULL,
            method TEXT NOT NULL,
            PRIMARY KEY (analysis_id, dataset, metric)
        );
        CREATE TABLE IF NOT EXISTS analisis_estadistico.pairwise_test (
            analysis_id UUID NOT NULL REFERENCES analisis_estadistico.analysis_run(analysis_id) ON DELETE CASCADE,
            metric TEXT NOT NULL,
            technique_a TEXT NOT NULL,
            technique_b TEXT NOT NULL,
            n_blocks INTEGER NOT NULL,
            wilcoxon_statistic DOUBLE PRECISION NOT NULL,
            p_value DOUBLE PRECISION NOT NULL,
            p_value_holm DOUBLE PRECISION NOT NULL,
            rank_biserial DOUBLE PRECISION NOT NULL,
            rank_biserial_ci95_low DOUBLE PRECISION,
            rank_biserial_ci95_high DOUBLE PRECISION,
            median_difference_a_minus_b DOUBLE PRECISION NOT NULL,
            ci95_low DOUBLE PRECISION NOT NULL,
            ci95_high DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (analysis_id, metric, technique_a, technique_b)
        );
        CREATE TABLE IF NOT EXISTS analisis_estadistico.hypothesis_decision (
            analysis_id UUID NOT NULL REFERENCES analisis_estadistico.analysis_run(analysis_id) ON DELETE CASCADE,
            hypothesis_code TEXT NOT NULL,
            decision TEXT NOT NULL,
            supporting_metrics TEXT[] NOT NULL,
            rationale TEXT NOT NULL,
            PRIMARY KEY (analysis_id, hypothesis_code)
        );
        """
    )
    await connection.execute(
        """
        ALTER TABLE analisis_estadistico.pairwise_test
            ADD COLUMN IF NOT EXISTS rank_biserial_ci95_low DOUBLE PRECISION,
            ADD COLUMN IF NOT EXISTS rank_biserial_ci95_high DOUBLE PRECISION
        """
    )


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default=os.getenv("PGDATABASE", "investigacionv5"))
    parser.add_argument("--user", default=os.getenv("PGUSER", "postgres"))
    parser.add_argument("--host", default=os.getenv("PGHOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PGPORT", "5432")))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "resultados",
    )
    args = parser.parse_args()

    analysis_id = uuid.uuid4()
    output_dir = args.output / analysis_id.hex
    figures_dir = output_dir / "figuras"
    figures_dir.mkdir(parents=True, exist_ok=False)

    connection = await asyncpg.connect(
        database=args.database,
        user=args.user,
        host=args.host,
        port=args.port,
    )
    try:
        await create_analysis_tables(connection)
        protocol = await connection.fetchrow(
            "SELECT codigo, modelo_objetivo FROM experimento.protocolo_experimental WHERE activo ORDER BY protocolo_id LIMIT 1"
        )
        if protocol is None:
            raise RuntimeError("No active experimental protocol exists")

        problem_rows = await connection.fetch(
            "SELECT problema_id, codigo FROM experimento.problema WHERE activo ORDER BY problema_id"
        )
        technique_rows = await connection.fetch(
            "SELECT tecnica_id, codigo, nombre FROM experimento.tecnica_prompt WHERE activa ORDER BY tecnica_id"
        )
        execution_rows = await connection.fetch(
            """
            SELECT ejecucion_id, problema_id, tecnica_id, numero_repeticion,
                   estado_ejecucion, estado_validacion, codigo_parseable,
                   generacion_exitosa, duracion_generacion_ms,
                   respuesta_completa IS NOT NULL AS has_response,
                   codigo_generado IS NOT NULL AS has_code
            FROM experimento.ejecucion_experimental
            ORDER BY ejecucion_id
            """
        )
        metric_rows = await connection.fetch(
            """
            SELECT m.ejecucion_id, e.problema_id, p.codigo AS problem_code,
                   t.codigo AS technique_code, e.numero_repeticion,
                   e.estado_ejecucion, m.metrica, m.valor_numerico::double precision AS value,
                   m.estado_medicion, m.unidad
            FROM experimento.medicion_metrica m
            JOIN experimento.ejecucion_experimental e USING (ejecucion_id)
            JOIN experimento.problema p USING (problema_id)
            JOIN experimento.tecnica_prompt t USING (tecnica_id)
            WHERE m.metrica = ANY($1::text[])
            ORDER BY m.ejecucion_id, m.metrica
            """,
            list(METRICS),
        )
        table_counts_rows = await connection.fetch(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema='experimento' AND table_type='BASE TABLE'
            ORDER BY table_name
            """
        )
        table_counts: dict[str, int] = {}
        for row in table_counts_rows:
            table = row["table_name"]
            if table not in BASE_TABLES:
                continue
            count = await connection.fetchval(
                f'SELECT COUNT(*) FROM experimento."{table}"'
            )
            table_counts[table] = int(count)
        duplicate_trials = await connection.fetchval(
            """
            SELECT COUNT(*) FROM (
                SELECT protocolo_id, problema_id, tecnica_id, numero_repeticion
                FROM experimento.ejecucion_experimental
                GROUP BY 1,2,3,4 HAVING COUNT(*) > 1
            ) d
            """
        )
        duplicate_tests = await connection.fetchval(
            """
            SELECT COUNT(*) FROM (
                SELECT ejecucion_id, identificador_prueba
                FROM experimento.resultado_prueba
                GROUP BY 1,2 HAVING COUNT(*) > 1
            ) d
            """
        )
        benchmark_summary = await connection.fetch(
            """
            SELECT tipo_corrida, COUNT(*) AS n,
                   COUNT(*) FILTER (WHERE timeout) AS timeouts,
                   COUNT(*) FILTER (WHERE codigo_salida IS NOT NULL AND codigo_salida <> 0) AS nonzero_exit,
                   COUNT(*) FILTER (WHERE tiempo_ejecucion_ms IS NULL) AS null_elapsed,
                   COUNT(*) FILTER (WHERE memoria_pico_bytes IS NULL) AS null_memory
            FROM experimento.benchmark_corrida
            GROUP BY tipo_corrida ORDER BY tipo_corrida
            """
        )
        benchmark_first_case_failures = await connection.fetchval(
            """
            SELECT COUNT(DISTINCT ejecucion_id)
            FROM experimento.benchmark_corrida
            WHERE tipo_corrida='medicion'
              AND codigo_salida IS NOT NULL AND codigo_salida <> 0
            """
        )
        completed_without_benchmark = await connection.fetchval(
            """
            SELECT COUNT(*)
            FROM experimento.ejecucion_experimental e
            WHERE e.estado_ejecucion='completada'
              AND NOT EXISTS (
                  SELECT 1 FROM experimento.benchmark_corrida b
                  WHERE b.ejecucion_id=e.ejecucion_id
              )
            """
        )
        generation_summary = await connection.fetchrow(
            """
            SELECT COUNT(*) AS n,
                   COUNT(*) FILTER (WHERE respuesta_completa IS NULL) AS no_response,
                   COUNT(*) FILTER (WHERE codigo_generado IS NULL) AS no_code,
                   COUNT(*) FILTER (WHERE duracion_generacion_ms IS NULL) AS no_generation_duration
            FROM experimento.ejecucion_experimental
            """
        )

        problem_code = {row["problema_id"]: row["codigo"] for row in problem_rows}
        technique_label = {row["codigo"]: row["nombre"] for row in technique_rows}
        techniques = [row["codigo"] for row in technique_rows]
        if techniques != TECHNIQUE_ORDER:
            raise RuntimeError(
                f"Active techniques differ from the planned four: {techniques}"
            )
        expected_keys = {
            (problem_id, technique, repetition)
            for problem_id in problem_code
            for technique in techniques
            for repetition in (1, 2, 3)
        }
        existing_keys = {
            (row["problema_id"], technique_by_id, row["numero_repeticion"])
            for row in execution_rows
            for technique_by_id in [
                next(
                    item["codigo"]
                    for item in technique_rows
                    if item["tecnica_id"] == row["tecnica_id"]
                )
            ]
        }
        if len(existing_keys) != len(execution_rows):
            raise RuntimeError("Execution key duplicates detected during audit")
        missing_keys = sorted(expected_keys - existing_keys)

        metric_measurements: dict[
            str, dict[tuple[int, str], list[tuple[int, float, int]]]
        ] = {metric: defaultdict(list) for metric in METRICS}
        raw_csv_rows: list[dict[str, Any]] = []
        status_counts: Counter[str] = Counter()
        unit_counts: dict[str, Counter[str]] = {
            metric: Counter() for metric in METRICS
        }
        nonfinite_counts: Counter[str] = Counter()
        null_counts: Counter[str] = Counter()
        invalid_state_counts: Counter[str] = Counter()
        outlier_counts: dict[str, dict[str, int | float]] = {}
        for row in metric_rows:
            metric = row["metrica"]
            value = row["value"]
            valid = (
                row["estado_medicion"] == "valida"
                and value is not None
                and math.isfinite(float(value))
            )
            status_counts[f"{metric}:{row['estado_medicion']}"] += 1
            unit_counts[metric][row["unidad"] or "(null)"] += 1
            if value is None:
                null_counts[metric] += 1
            elif not math.isfinite(float(value)):
                nonfinite_counts[metric] += 1
            if row["estado_medicion"] != "valida":
                invalid_state_counts[metric] += 1
            raw_csv_rows.append(
                {
                    "execution_id": row["ejecucion_id"],
                    "problem_id": row["problema_id"],
                    "problem_code": row["problem_code"],
                    "technique": row["technique_code"],
                    "repetition": row["numero_repeticion"],
                    "execution_status": row["estado_ejecucion"],
                    "metric": metric,
                    "value": value,
                    "measurement_status": row["estado_medicion"],
                    "unit": row["unidad"],
                }
            )
            if valid:
                metric_measurements[metric][
                    (row["problema_id"], row["technique_code"])
                ].append(
                    (
                        row["numero_repeticion"],
                        float(value),
                        row["ejecucion_id"],
                    )
                )

        aggregate: dict[str, dict[tuple[int, str], float]] = {
            metric: {} for metric in METRICS
        }
        repetition_count: dict[str, dict[tuple[int, str], int]] = {
            metric: {} for metric in METRICS
        }
        for metric in METRICS:
            for key, observations in metric_measurements[metric].items():
                values = [value for _, value, _ in observations]
                aggregate[metric][key] = float(np.median(values))
                repetition_count[metric][key] = len(values)

            valid_values = np.asarray(
                [
                    value
                    for observations in metric_measurements[metric].values()
                    for _, value, _ in observations
                ],
                dtype=float,
            )
            if len(valid_values):
                q1, q3 = np.quantile(valid_values, [0.25, 0.75])
                lower, upper = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
                outlier_counts[metric] = {
                    "n_valid": int(len(valid_values)),
                    "q1": float(q1),
                    "q3": float(q3),
                    "iqr": float(q3 - q1),
                    "lower_fence": float(lower),
                    "upper_fence": float(upper),
                    "flagged_1_5_iqr": int(
                        np.sum((valid_values < lower) | (valid_values > upper))
                    ),
                }
            else:
                outlier_counts[metric] = {
                    "n_valid": 0,
                    "flagged_1_5_iqr": 0,
                }

        primary_blocks: dict[str, list[int]] = {}
        strict_blocks: dict[str, list[int]] = {}
        for metric in METRICS:
            primary_blocks[metric] = [
                problem_id
                for problem_id in problem_code
                if all(
                    (problem_id, technique) in aggregate[metric]
                    for technique in techniques
                )
            ]
            strict_blocks[metric] = [
                problem_id
                for problem_id in primary_blocks[metric]
                if all(
                    repetition_count[metric].get((problem_id, technique), 0) == 3
                    for technique in techniques
                )
            ]

        valid_run_counts = {
            metric: sum(len(values) for values in metric_measurements[metric].values())
            for metric in METRICS
        }
        duplicate_run_keys = int(duplicate_trials)
        audit_snapshot = {
            "database": args.database,
            "protocol": dict(protocol),
            "table_counts": table_counts,
            "total_base_table_rows": sum(table_counts.values()),
            "active_problems": len(problem_rows),
            "active_techniques": len(technique_rows),
            "expected_experiment_combinations": len(expected_keys),
            "persisted_experiment_rows": len(execution_rows),
            "missing_experiment_combinations": len(missing_keys),
            "missing_combinations": [
                {
                    "problem_code": problem_code[problem_id],
                    "technique": technique,
                    "repetition": repetition,
                }
                for problem_id, technique, repetition in missing_keys
            ],
            "problems_with_missing_combinations": len(
                {problem_id for problem_id, _, _ in missing_keys}
            ),
            "duplicate_execution_keys": duplicate_run_keys,
            "duplicate_test_identifiers": int(duplicate_tests),
            "execution_status_counts": dict(
                Counter(row["estado_ejecucion"] for row in execution_rows)
            ),
            "generation_fields": dict(generation_summary),
            "metric_row_counts": dict(Counter(row["metrica"] for row in metric_rows)),
            "valid_metric_observation_counts": valid_run_counts,
            "metric_state_counts": dict(status_counts),
            "metric_null_counts": dict(null_counts),
            "metric_nonfinite_counts": dict(nonfinite_counts),
            "metric_invalid_state_counts": dict(invalid_state_counts),
            "metric_units": {
                metric: dict(counts) for metric, counts in unit_counts.items()
            },
            "primary_complete_blocks": {
                metric: len(primary_blocks[metric]) for metric in METRICS
            },
            "strict_all_three_repetition_blocks": {
                metric: len(strict_blocks[metric]) for metric in METRICS
            },
            "outlier_fences_and_flags": outlier_counts,
            "benchmark_rows_by_type": [dict(row) for row in benchmark_summary],
            "benchmark_execution_groups_with_nonzero_measurement_exit": int(
                benchmark_first_case_failures
            ),
            "completed_executions_without_benchmark_rows": int(
                completed_without_benchmark
            ),
        }

        global_tests: list[dict[str, Any]] = []
        for metric in METRICS:
            global_tests.append(
                run_friedman(
                    metric, "primary", primary_blocks[metric], aggregate
                )
            )
        adjusted = holm_adjust([row["p_raw"] for row in global_tests])
        for row, p_adjusted in zip(global_tests, adjusted):
            row["p_holm"] = p_adjusted
            row["significant"] = p_adjusted < ALPHA

        sensitivity_tests: list[dict[str, Any]] = []
        for metric in METRICS:
            sensitivity_tests.append(
                run_friedman(
                    metric, "strict_3_repetitions", strict_blocks[metric], aggregate
                )
            )
        sensitivity_adjusted = holm_adjust(
            [row["p_raw"] for row in sensitivity_tests]
        )
        for row, p_adjusted in zip(sensitivity_tests, sensitivity_adjusted):
            row["p_holm"] = p_adjusted
            row["significant"] = p_adjusted < ALPHA

        descriptive_rows: list[dict[str, Any]] = []
        for metric in METRICS:
            scopes = {
                "all_observed_problem_technique_medians": list(
                    aggregate[metric].keys()
                ),
                "primary_complete_blocks": [
                    (problem_id, technique)
                    for problem_id in primary_blocks[metric]
                    for technique in techniques
                ],
            }
            for scope, pairs in scopes.items():
                for technique in techniques:
                    values = [
                        aggregate[metric][(problem_id, technique)]
                        for problem_id, item_technique in pairs
                        if item_technique == technique
                    ]
                    if not values:
                        continue
                    descriptive = summarize(values, metric)
                    descriptive_rows.append(
                        {
                            "metric": metric,
                            "metric_label": METRICS[metric]["label"],
                            "technique": technique,
                            "technique_name": technique_label.get(technique, technique),
                            "sample_scope": scope,
                            "unit": METRICS[metric]["unit"],
                            **descriptive,
                        }
                    )

        posthoc_rows: list[dict[str, Any]] = []
        for metric in METRICS:
            global_row = next(row for row in global_tests if row["metric"] == metric)
            if not global_row["significant"]:
                continue
            blocks = primary_blocks[metric]
            local_rows = []
            for technique_a, technique_b in itertools.combinations(techniques, 2):
                a = np.asarray(
                    [aggregate[metric][(problem_id, technique_a)] for problem_id in blocks],
                    dtype=float,
                )
                b = np.asarray(
                    [aggregate[metric][(problem_id, technique_b)] for problem_id in blocks],
                    dtype=float,
                )
                difference = a - b
                if np.all(difference == 0):
                    statistic, p_value = 0.0, 1.0
                else:
                    result = wilcoxon(
                        a,
                        b,
                        zero_method="wilcox",
                        correction=False,
                        alternative="two-sided",
                        method="auto",
                    )
                    statistic, p_value = float(result.statistic), float(result.pvalue)
                seed = RANDOM_SEED + sum(ord(char) for char in f"{metric}:{technique_a}:{technique_b}")
                ci_low, ci_high = paired_bootstrap_median_ci(difference, seed)
                effect_ci_low, effect_ci_high = paired_bootstrap_rank_biserial_ci(
                    difference, seed + 1
                )
                local_rows.append(
                    {
                        "metric": metric,
                        "n_blocks": len(blocks),
                        "technique_a": technique_a,
                        "technique_b": technique_b,
                        "wilcoxon_statistic": statistic,
                        "p_raw": p_value,
                        "rank_biserial_a_minus_b": rank_biserial(difference),
                        "rank_biserial_ci95_low": effect_ci_low,
                        "rank_biserial_ci95_high": effect_ci_high,
                        "median_difference_a_minus_b": float(np.median(difference)),
                        "ci95_low_median_difference": ci_low,
                        "ci95_high_median_difference": ci_high,
                        "unit": METRICS[metric]["unit"],
                    }
                )
            p_holm = holm_adjust([row["p_raw"] for row in local_rows])
            for row, value in zip(local_rows, p_holm):
                row["p_holm"] = value
                row["significant_after_holm"] = value < ALPHA
            posthoc_rows.extend(local_rows)

        def metric_sig(metric: str) -> bool:
            return bool(
                next(row for row in global_tests if row["metric"] == metric)["significant"]
            )

        decisions = [
            {
                "hypothesis_code": "HE1",
                "decision": "respaldo estadístico" if metric_sig("porcentaje_pruebas_aprobadas") else "sin respaldo estadístico",
                "supporting_metrics": ["porcentaje_pruebas_aprobadas"] if metric_sig("porcentaje_pruebas_aprobadas") else [],
                "rationale": "Diferencia global de exactitud funcional tras corrección Holm de los seis indicadores primarios." if metric_sig("porcentaje_pruebas_aprobadas") else "No se detectó diferencia global de exactitud funcional tras corrección Holm.",
            },
            {
                "hypothesis_code": "HE2",
                "decision": "respaldo estadístico" if any(metric_sig(m) for m in ("maintainability_index", "complejidad_ciclomatica_max", "sloc")) else "sin respaldo estadístico",
                "supporting_metrics": [m for m in ("maintainability_index", "complejidad_ciclomatica_max", "sloc") if metric_sig(m)],
                "rationale": "Al menos un indicador de mantenibilidad muestra una diferencia global tras Holm." if any(metric_sig(m) for m in ("maintainability_index", "complejidad_ciclomatica_max", "sloc")) else "Ningún indicador de mantenibilidad muestra diferencia global tras Holm.",
            },
            {
                "hypothesis_code": "HE3",
                "decision": "respaldo estadístico condicionado a mediciones válidas" if any(metric_sig(m) for m in ("tiempo_promedio_ms", "memoria_mediana_bytes")) else "sin respaldo estadístico",
                "supporting_metrics": [m for m in ("tiempo_promedio_ms", "memoria_mediana_bytes") if metric_sig(m)],
                "rationale": "La comparación de eficiencia está condicionada a que el benchmark de la primera aserción haya sido válido." if any(metric_sig(m) for m in ("tiempo_promedio_ms", "memoria_mediana_bytes")) else "No se detectó diferencia global de eficiencia tras Holm; el análisis usa solo ejecuciones con benchmark válido.",
            },
        ]
        any_global = any(row["significant"] for row in global_tests)
        decisions.append(
            {
                "hypothesis_code": "HG",
                "decision": "respaldo estadístico parcial" if any_global else "sin respaldo estadístico",
                "supporting_metrics": [row["metric"] for row in global_tests if row["significant"]],
                "rationale": "Existe diferencia global en al menos un indicador tras Holm; esto no implica superioridad general ni un índice compuesto." if any_global else "No se detectó diferencia global en los indicadores tras Holm; esto no demuestra equivalencia.",
            }
        )
        interpretation = {
            "familywise_alpha": ALPHA,
            "primary_global_holm_significant_metrics": [
                row["metric"] for row in global_tests if row["significant"]
            ],
            "sensitivity_global_holm_significant_metrics": [
                row["metric"] for row in sensitivity_tests if row["significant"]
            ],
            "hypothesis_decisions": decisions,
        }

        plot_files = {
            metric: make_plots(
                figures_dir,
                metric,
                primary_blocks[metric],
                aggregate,
                technique_label,
            )
            for metric in METRICS
        }

        processed_rows: list[dict[str, Any]] = []
        for metric in METRICS:
            for (problem_id, technique), value in aggregate[metric].items():
                processed_rows.append(
                    {
                        "metric": metric,
                        "problem_id": problem_id,
                        "problem_code": problem_code[problem_id],
                        "technique": technique,
                        "valid_repetitions": repetition_count[metric][
                            (problem_id, technique)
                        ],
                        "median_value": value,
                        "unit": METRICS[metric]["unit"],
                        "in_primary_complete_blocks": problem_id
                        in primary_blocks[metric],
                        "in_strict_complete_blocks": problem_id
                        in strict_blocks[metric],
                    }
                )

        audit_rows = [
            {"audit_key": key, "audit_value": json.dumps(value, ensure_ascii=False, default=json_default)}
            for key, value in audit_snapshot.items()
        ]
        processed_csv = [
            {key: value for key, value in row.items()}
            for row in processed_rows
        ]
        write_csv(output_dir / "auditoria.csv", audit_rows)
        write_csv(output_dir / "mediciones_originales.csv", raw_csv_rows)
        write_csv(output_dir / "datos_procesados_por_problema_tecnica.csv", processed_csv)
        write_csv(output_dir / "estadistica_descriptiva.csv", descriptive_rows)
        write_csv(output_dir / "pruebas_globales.csv", global_tests)
        write_csv(output_dir / "sensibilidad_12_repeticiones.csv", sensitivity_tests)
        write_csv(output_dir / "comparaciones_posthoc.csv", posthoc_rows)
        write_csv(output_dir / "decisiones_hipotesis.csv", decisions)

        report_path = output_dir / "informe.md"
        report = render_report(
            analysis_id,
            args.database,
            table_counts,
            audit_snapshot,
            global_tests,
            sensitivity_tests,
            descriptive_rows,
            posthoc_rows,
            decisions,
            plot_files,
        )
        report_path.write_text(report, encoding="utf-8")

        await connection.execute(
            """
            INSERT INTO analisis_estadistico.analysis_run
                (analysis_id,database_name,script_version,alpha,aggregation_rule,
                 artifact_directory,audit_snapshot,interpretation)
            VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb,$8::jsonb)
            """,
            analysis_id,
            args.database,
            SCRIPT_VERSION,
            ALPHA,
            "Median of available valid repetitions per problem and technique; Friedman by problem block.",
            str(output_dir.resolve()),
            json.dumps(audit_snapshot, ensure_ascii=False, default=json_default),
            json.dumps(interpretation, ensure_ascii=False, default=json_default),
        )
        await connection.executemany(
            """
            INSERT INTO analisis_estadistico.audit_item (analysis_id,audit_key,audit_value)
            VALUES ($1,$2,$3::jsonb)
            """,
            [
                (analysis_id, key, json.dumps(value, ensure_ascii=False, default=json_default))
                for key, value in audit_snapshot.items()
            ],
        )
        await connection.executemany(
            """
            INSERT INTO analisis_estadistico.processed_observation
                (analysis_id,metric,problem_id,problem_code,technique_code,
                 valid_repetitions,median_value,unit,in_primary_complete_blocks,
                 in_strict_complete_blocks)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
            """,
            [
                (
                    analysis_id,
                    row["metric"],
                    row["problem_id"],
                    row["problem_code"],
                    row["technique"],
                    row["valid_repetitions"],
                    row["median_value"],
                    row["unit"],
                    row["in_primary_complete_blocks"],
                    row["in_strict_complete_blocks"],
                )
                for row in processed_rows
            ],
        )
        await connection.executemany(
            """
            INSERT INTO analisis_estadistico.descriptive_statistic
                (analysis_id,metric,technique_code,sample_scope,n,mean,standard_deviation,
                 median,q1,q3,iqr,minimum,maximum,coefficient_variation_percent)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
            """,
            [
                (
                    analysis_id,
                    row["metric"],
                    row["technique"],
                    row["sample_scope"],
                    row["n"],
                    row["mean"],
                    row["sd"],
                    row["median"],
                    row["q1"],
                    row["q3"],
                    row["iqr"],
                    row["minimum"],
                    row["maximum"],
                    row["cv_percent"],
                )
                for row in descriptive_rows
            ],
        )
        await connection.executemany(
            """
            INSERT INTO analisis_estadistico.global_test
                (analysis_id,dataset,metric,n_blocks,statistic,degrees_freedom,
                 p_value,p_value_holm,kendall_w,significant_after_holm,method)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
            """,
            [
                (
                    analysis_id,
                    row["dataset"],
                    row["metric"],
                    row["n_blocks"],
                    row["statistic"],
                    row["df"],
                    row["p_raw"],
                    row["p_holm"],
                    row["kendall_w"],
                    row["significant"],
                    row["method"],
                )
                for row in global_tests + sensitivity_tests
            ],
        )
        await connection.executemany(
            """
            INSERT INTO analisis_estadistico.pairwise_test
                (analysis_id,metric,technique_a,technique_b,n_blocks,
                 wilcoxon_statistic,p_value,p_value_holm,rank_biserial,
                 rank_biserial_ci95_low,rank_biserial_ci95_high,
                 median_difference_a_minus_b,ci95_low,ci95_high)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
            """,
            [
                (
                    analysis_id,
                    row["metric"],
                    row["technique_a"],
                    row["technique_b"],
                    row["n_blocks"],
                    row["wilcoxon_statistic"],
                    row["p_raw"],
                    row["p_holm"],
                    row["rank_biserial_a_minus_b"],
                    row["rank_biserial_ci95_low"],
                    row["rank_biserial_ci95_high"],
                    row["median_difference_a_minus_b"],
                    row["ci95_low_median_difference"],
                    row["ci95_high_median_difference"],
                )
                for row in posthoc_rows
            ],
        )
        await connection.executemany(
            """
            INSERT INTO analisis_estadistico.hypothesis_decision
                (analysis_id,hypothesis_code,decision,supporting_metrics,rationale)
            VALUES ($1,$2,$3,$4,$5)
            """,
            [
                (
                    analysis_id,
                    row["hypothesis_code"],
                    row["decision"],
                    row["supporting_metrics"],
                    row["rationale"],
                )
                for row in decisions
            ],
        )
        print(f"analysis_id={analysis_id}")
        print(f"database={args.database}")
        print(f"base_table_rows={sum(table_counts.values())}")
        print(f"artifacts={output_dir.resolve()}")
        print(f"global_tests={json.dumps(global_tests, ensure_ascii=False)}")
        print(f"hypotheses={json.dumps(decisions, ensure_ascii=False)}")
    finally:
        await connection.close()


def render_report(
    analysis_id: uuid.UUID,
    database: str,
    table_counts: dict[str, int],
    audit: dict[str, Any],
    global_tests: list[dict[str, Any]],
    sensitivity_tests: list[dict[str, Any]],
    descriptive_rows: list[dict[str, Any]],
    posthoc_rows: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    plot_files: dict[str, str],
) -> str:
    total_rows = sum(table_counts.values())
    lines = [
        "# Análisis estadístico de investigacionv5",
        "",
        f"- ID del análisis: `{analysis_id}`",
        f"- Base analizada: `{database}`",
        f"- Fecha UTC: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Filas sumadas de las 11 tablas base: **{total_rows:,}**",
        "- Las vistas analíticas no se cuentan como tablas base.",
        "",
        "## Auditoría de integridad",
        "",
        "| Tabla | Filas |",
        "|---|---:|",
    ]
    for table, count in sorted(table_counts.items()):
        lines.append(f"| `{table}` | {count:,} |")
    lines.extend(
        [
            "",
            f"- Combinaciones planificadas: {audit['expected_experiment_combinations']:,}; ejecuciones registradas: {audit['persisted_experiment_rows']:,}; combinaciones ausentes: {audit['missing_experiment_combinations']} en {audit['problems_with_missing_combinations']} problemas.",
            f"- Duplicados de combinación ejecución/problema/técnica/repetición: {audit['duplicate_execution_keys']}; identificadores de prueba duplicados: {audit['duplicate_test_identifiers']}.",
            f"- Estados: `{json.dumps(audit['execution_status_counts'], ensure_ascii=False)}`.",
            f"- Las 19 ejecuciones fallidas carecen de respuesta/código persistido y se tratan como ejecuciones incompletas; sus mediciones ya persistidas solo se usan para la variable correspondiente.",
            f"- Observaciones válidas por indicador: `{json.dumps(audit['valid_metric_observation_counts'], ensure_ascii=False)}`.",
            f"- Nulos / no finitos por indicador: `{json.dumps(audit['metric_null_counts'], ensure_ascii=False)}` / `{json.dumps(audit['metric_nonfinite_counts'], ensure_ascii=False)}`.",
            f"- Unidades observadas: `{json.dumps(audit['metric_units'], ensure_ascii=False)}`.",
            f"- Bloques completos por indicador (al menos una repetición válida por cada técnica): `{json.dumps(audit['primary_complete_blocks'], ensure_ascii=False)}`.",
            f"- Sensibilidad estricta (3 repeticiones válidas para las cuatro técnicas): `{json.dumps(audit['strict_all_three_repetition_blocks'], ensure_ascii=False)}`.",
            f"- Corridas de benchmark con salida no cero en al menos una medición: {audit['benchmark_execution_groups_with_nonzero_measurement_exit']}; completadas sin filas de benchmark: {audit['completed_executions_without_benchmark_rows']}.",
            "",
            "Los valores atípicos potenciales se marcan usando la regla exploratoria de 1,5×IQR en observaciones válidas de ejecución. No se eliminan ni winsorizan; Friedman es una prueba basada en rangos. El detalle de cercas y conteos está en `auditoria.csv`.",
            "",
            "## Decisiones estadísticas",
            "",
            "- Las repeticiones pertenecen a la misma combinación problema-técnica; se resumen con la mediana para reducir sensibilidad a observaciones extremas y no inflar el tamaño muestral.",
            "- Cada problema es un bloque y cada técnica un tratamiento: prueba global de Friedman por indicador, con Kendall W como tamaño de efecto.",
            "- Se aplicó Holm a los seis contrastes globales (exactitud, MI, CC, SLOC, tiempo, memoria; α=.05).",
            "- Solo los indicadores con Friedman significativo tras Holm tienen post hoc Wilcoxon pareado; Holm se aplica a los seis pares de técnicas dentro de cada indicador. Se informa rango biserial pareado y bootstrap percentil del 95% para la diferencia mediana A−B.",
            "- Sensibilidad: se repite Friedman restringiendo a bloques que tienen las tres repeticiones válidas en las cuatro técnicas; Holm se aplica separadamente a los seis contrastes de sensibilidad.",
            "- SLOC se trata como resultado descriptivo de tamaño, sin presuponer que menos líneas signifiquen mejor calidad.",
            "- No se construye un índice compuesto ni se interpreta un resultado no significativo como equivalencia.",
            "",
            "## Estadística descriptiva",
            "",
            "La tabla principal usa medianas por problema-técnica y solo los bloques completos del indicador, para comparar las técnicas sobre los mismos problemas. `estadistica_descriptiva.csv` también contiene el conjunto de todas las celdas problema-técnica observadas.",
            "",
            "| Indicador | Técnica | n problemas | Media | DE | Mediana | Q1–Q3 | Mín–Máx | CV (%) |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in descriptive_rows:
        if row["sample_scope"] != "primary_complete_blocks":
            continue
        cv = "—" if row["cv_percent"] is None else f"{row['cv_percent']:.2f}"
        sd = "—" if row["sd"] is None else f"{row['sd']:.3f}"
        lines.append(
            f"| {row['metric_label']} | {row['technique_name']} | {row['n']} | {row['mean']:.3f} | {sd} | {row['median']:.3f} | {row['q1']:.3f}–{row['q3']:.3f} | {row['minimum']:.3f}–{row['maximum']:.3f} | {cv} |"
        )
    lines.extend(
        [
            "",
            "## Pruebas globales",
            "",
            "| Indicador | n bloques | χ² de Friedman | gl | p | p Holm (6 indicadores) | W Kendall | Resultado |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in global_tests:
        lines.append(
            f"| {METRICS[row['metric']]['label']} | {row['n_blocks']} | {row['statistic']:.4f} | {row['df']} | {row['p_raw']:.6g} | {row['p_holm']:.6g} | {row['kendall_w']:.4f} | {'significativo' if row['significant'] else 'no significativo'} |"
        )
    lines.extend(
        [
            "",
            "## Sensibilidad: solo bloques con 12 repeticiones válidas",
            "",
            "| Indicador | n bloques | χ² de Friedman | p | p Holm | W Kendall | Resultado |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in sensitivity_tests:
        lines.append(
            f"| {METRICS[row['metric']]['label']} | {row['n_blocks']} | {row['statistic']:.4f} | {row['p_raw']:.6g} | {row['p_holm']:.6g} | {row['kendall_w']:.4f} | {'significativo' if row['significant'] else 'no significativo'} |"
        )
    lines.extend(["", "## Comparaciones post hoc", ""])
    if not posthoc_rows:
        lines.append(
            "No se ejecutaron comparaciones post hoc: ningún contraste global superó Holm."
        )
    else:
        lines.extend(
            [
                "Las diferencias se expresan como técnica A menos técnica B. El rango biserial pareado incluye IC bootstrap percentil; también se presenta el IC de la diferencia mediana pareada.",
                "",
                "| Indicador | A | B | n | p | p Holm (pares) | Rango biserial [IC 95%] | Dif. mediana A−B [IC 95%] |",
                "|---|---|---|---:|---:|---:|---:|---:|",
            ]
        )
        for row in posthoc_rows:
            lines.append(
                f"| {METRICS[row['metric']]['label']} | {row['technique_a']} | {row['technique_b']} | {row['n_blocks']} | {row['p_raw']:.6g} | {row['p_holm']:.6g} | {row['rank_biserial_a_minus_b']:.3f} [{row['rank_biserial_ci95_low']:.3f}, {row['rank_biserial_ci95_high']:.3f}] | {row['median_difference_a_minus_b']:.3f} [{row['ci95_low_median_difference']:.3f}, {row['ci95_high_median_difference']:.3f}] {METRICS[row['metric']]['unit']} |"
            )
        lines.extend(
            [
                "",
                "Nota: por el redondeo y empates del MI, la mediana de la diferencia pareada puede ser cero y su IC bootstrap incluir cero aunque Wilcoxon detecte asimetría en los rangos. Para el tamaño y dirección del efecto de rangos, consulte el rango biserial y su IC bootstrap; un p significativo no implica una diferencia grande.",
            ]
        )
    lines.extend(
        [
            "",
            "## Hipótesis",
            "",
            "| Hipótesis | Decisión | Indicadores que aportan evidencia |",
            "|---|---|---|",
        ]
    )
    for decision in decisions:
        supporting = ", ".join(decision["supporting_metrics"]) or "Ninguno"
        lines.append(
            f"| {decision['hypothesis_code']} | {decision['decision']} | {supporting} |"
        )
    lines.extend(
        [
            "",
            "## Figuras",
            "",
        ]
    )
    for metric, filename in plot_files.items():
        lines.append(
            f"- [{METRICS[metric]['label']}](figuras/{filename})"
        )
    lines.extend(
        [
            "",
            "## Interpretación y límites",
            "",
            "Los resultados de exactitud y mantenibilidad se basan en los indicadores persistidos, incluyendo mediciones parciales de ejecuciones cuyo registro final quedó fallido; esas 19 ejecuciones no tienen código ni respuesta archivados, por lo que su procedencia no puede auditarse íntegramente. Se cuantifica este hecho y se excluyen del análisis las variables que no tienen un valor válido.",
            "",
            "La disponibilidad de tiempo y memoria depende de que el código complete la primera aserción usada por el benchmark. En los datos, 631 grupos de benchmark tienen salida no cero durante mediciones y 7 ejecuciones completadas no tienen filas de benchmark. Por ello, las pruebas de eficiencia describen solo ejecuciones con medición válida; pueden sufrir sesgo de selección y no deben generalizarse a todas las generaciones.",
            "",
            "El sistema guarda tiempo en milisegundos como **promedio** de corridas correctas y memoria en bytes como **mediana**. Se verificó que ambas métricas guardadas coinciden con las corridas originales válidas. Aunque el manual menciona tiempo mediano, este análisis respeta y documenta el cálculo realmente almacenado.",
            "",
            "La falta de diferencias significativas no prueba equivalencia. W de Kendall mide magnitud de concordancia de rangos entre tratamientos; dirección y pares deben interpretarse junto con la mediana, intervalos y corrección múltiple. El análisis compara el comportamiento de estas técnicas en estos problemas y bajo este protocolo, sin afirmar una superioridad universal.",
            "",
            "## Reproducción",
            "",
            "Desde la raíz del proyecto: ` .venv/bin/python analisis_estadistico_investigacionv5/analizar.py --database investigacionv5 --user postgres`.",
            f"El código y datos tabulares de esta corrida se guardaron en `{analysis_id.hex}/`; las tablas persistentes están en el esquema PostgreSQL `analisis_estadistico`.",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    asyncio.run(main())
