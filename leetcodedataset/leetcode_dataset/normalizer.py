from __future__ import annotations

import re
from datetime import date, datetime
from typing import Iterable, List, Optional

from .models import ProblemRecord


def normalize_difficulty(value: str) -> str:
    text = (value or "").strip().lower()
    aliases = {
        "easy": "Easy",
        "medium": "Medium",
        "hard": "Hard",
        "1": "Easy",
        "2": "Medium",
        "3": "Hard",
    }
    return aliases.get(text, value or "Unknown")


def parse_publication_date(value: Optional[str]) -> Optional[date]:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    raw = raw.replace("Z", "+00:00")
    for fmt in (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    match = re.search(r"(\d{4}-\d{2}-\d{2})", raw)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y-%m-%d").date()
        except ValueError:
            pass
    return None


def deduplicate(records: Iterable[ProblemRecord]) -> List[ProblemRecord]:
    seen: dict[str, ProblemRecord] = {}
    for record in records:
        key = record.key
        if key not in seen:
            seen[key] = record
            continue
        existing = seen[key]
        seen[key] = merge_two_records(existing, record)
    return list(seen.values())


def merge_two_records(first: ProblemRecord, second: ProblemRecord) -> ProblemRecord:
    merged = ProblemRecord(
        leetcode_id=first.leetcode_id or second.leetcode_id,
        title=first.title or second.title,
        slug=first.slug or second.slug,
        url=first.url or second.url,
        description=(first.description or second.description),
        difficulty=first.difficulty if first.difficulty != "Unknown" else second.difficulty,
        publication_date=first.publication_date or second.publication_date,
        date_type=first.date_type if first.date_type != "unknown" else second.date_type,
        original_date_field=first.original_date_field or second.original_date_field,
        source_name=first.source_name or second.source_name,
        source_url=first.source_url or second.source_url,
        extracted_at=first.extracted_at,
        tags=list(dict.fromkeys((first.tags or []) + (second.tags or []))),
        constraints=first.constraints or second.constraints,
        examples=first.examples or second.examples,
        signature=first.signature or second.signature,
        test_cases=first.test_cases or second.test_cases,
        reference_solution=first.reference_solution or second.reference_solution,
        source_license=first.source_license or second.source_license,
        completeness=first.completeness if len(first.description or "") >= len(second.description or "") else second.completeness,
        date_conflicts=[],
        notes=(first.notes or "") + ("; " if first.notes and second.notes else "") + (second.notes or ""),
    )

    dates = [d for d in [first.publication_date, second.publication_date] if d]
    unique_dates = sorted(set(dates))
    if len(unique_dates) > 1:
        merged.date_conflicts = unique_dates
        merged.date_type = "disputed"
        merged.notes = "Multiple publication dates were reported for this problem; it is excluded from the main verified set."
    return merged


def normalize_record(record: ProblemRecord) -> ProblemRecord:
    record.title = (record.title or "").strip()
    record.slug = (record.slug or record.title.lower().replace(" ", "-")).strip()
    record.url = record.url or f"https://leetcode.com/problems/{record.slug}/"
    record.difficulty = normalize_difficulty(record.difficulty)
    if record.publication_date:
        parsed_date = parse_publication_date(record.publication_date)
        record.publication_date = parsed_date.isoformat() if parsed_date else record.publication_date
    if record.description:
        record.completeness = "complete" if len(record.description.strip()) > 160 else "partial"
    return record
