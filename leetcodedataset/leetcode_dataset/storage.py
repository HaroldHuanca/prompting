from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from .models import ProblemRecord


def ensure_directory(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def write_csv(rows: Iterable[dict], target: str | Path) -> None:
    rows_list = list(rows)
    if not rows_list:
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        Path(target).write_text("", encoding="utf-8")
        return
    fieldnames = list(rows_list[0].keys())
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_list)


def write_records_csv(records: Iterable[ProblemRecord], target: str | Path) -> None:
    rows = [record.as_csv_row() for record in records]
    write_csv(rows, target)


def write_json(records: Iterable[ProblemRecord], target: str | Path) -> None:
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [record.as_csv_row() for record in records]
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
