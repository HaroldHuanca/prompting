from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, List

from .collector import collect_problem_records
from .normalizer import deduplicate, normalize_record
from .storage import ensure_directory, write_json, write_records_csv


REFERENCE_DATE = date(2024, 8, 6)


def split_by_time(records: Iterable) -> tuple[list, list, list]:
    official_after: list = []
    estimated_after: list = []
    without_verified: list = []
    for record in records:
        if record.date_conflicts:
            without_verified.append(record)
            continue
        if not record.publication_date:
            without_verified.append(record)
            continue
        parsed = date.fromisoformat(record.publication_date)
        if parsed > REFERENCE_DATE and record.date_type == "official":
            official_after.append(record)
        elif parsed > REFERENCE_DATE and record.date_type == "estimated":
            estimated_after.append(record)
        elif record.date_type in {"unknown", "disputed"}:
            without_verified.append(record)
    return official_after, estimated_after, without_verified


def summarize_problems(records: Iterable) -> dict[str, Any]:
    rows = list(records)
    counts = {
        "total": len(rows),
        "by_difficulty": {},
        "official_after_reference": 0,
        "estimated_after_reference": 0,
        "without_verified_date": 0,
        "with_complete_description": 0,
        "automatically_evaluable": 0,
        "python_compatible": 0,
    }
    for record in rows:
        difficulty = record.difficulty or "Unknown"
        counts["by_difficulty"][difficulty] = counts["by_difficulty"].get(difficulty, 0) + 1
        if record.description and len(record.description.strip()) > 80:
            counts["with_complete_description"] += 1
        if record.signature or record.examples or record.constraints:
            counts["automatically_evaluable"] += 1
        signature_lower = (record.signature or "").lower()
        if record.description and ("python" in signature_lower or "def " in signature_lower or "class solution" in signature_lower):
            counts["python_compatible"] += 1

    official_after, estimated_after, without_verified = split_by_time(rows)
    counts["official_after_reference"] = len(official_after)
    counts["estimated_after_reference"] = len(estimated_after)
    counts["without_verified_date"] = len(without_verified)
    return counts


def normalize_records(records: Iterable) -> List:
    normalized = []
    for record in records:
        normalized.append(normalize_record(record))
    return deduplicate(normalized)


def build_dataset(output_dir: str = "data") -> dict[str, Any]:
    output_path = Path(output_dir)
    ensure_directory(output_path)
    cache_dir = output_path / ".cache"
    ensure_directory(cache_dir)

    records = normalize_records(collect_problem_records())
    official_after, estimated_after, without_verified = split_by_time(records)
    summary = summarize_problems(records)

    source_manifest = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "leetcode_api + fallback_sample",
        "reference_date": "2024-08-06",
        "total_records": len(records),
        "official_after_reference": len(official_after),
        "estimated_after_reference": len(estimated_after),
        "without_verified_date": len(without_verified),
    }
    (cache_dir / "source_manifest.json").write_text(json.dumps(source_manifest, indent=2), encoding="utf-8")

    write_records_csv(records, output_path / "problems_normalized.csv")
    write_records_csv(official_after, output_path / "problems_after_reference.csv")
    write_records_csv(estimated_after, output_path / "problems_after_reference_estimated.csv")
    write_records_csv(without_verified, output_path / "problems_without_verified_date.csv")
    write_json(records, output_path / "problems_normalized.json")
    write_json(official_after, output_path / "problems_after_reference.json")
    write_json(estimated_after, output_path / "problems_after_reference_estimated.json")
    write_json(without_verified, output_path / "problems_without_verified_date.json")

    summary["total_after_reference"] = len(official_after) + len(estimated_after)
    summary["total_collected"] = len(records)
    summary["distribution"] = {
        "official_after_reference": len(official_after),
        "estimated_after_reference": len(estimated_after),
        "without_verified_date": len(without_verified),
    }
    summary["source_manifest"] = source_manifest
    return summary


class DatasetBuilder:
    def __init__(self, output_dir: str = "data"):
        self.output_dir = output_dir

    def run(self) -> dict[str, Any]:
        return build_dataset(self.output_dir)
