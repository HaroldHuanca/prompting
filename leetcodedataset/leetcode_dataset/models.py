from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class ProblemRecord:
    leetcode_id: Optional[str]
    title: str
    slug: str
    url: str
    description: str = ""
    difficulty: str = "Unknown"
    publication_date: Optional[str] = None
    date_type: str = "unknown"
    original_date_field: str = ""
    source_name: str = ""
    source_url: str = ""
    extracted_at: str = field(default_factory=utc_now_iso)
    tags: List[str] = field(default_factory=list)
    constraints: str = ""
    examples: str = ""
    signature: str = ""
    test_cases: str = ""
    reference_solution: str = ""
    source_license: str = ""
    completeness: str = "partial"
    date_conflicts: List[str] = field(default_factory=list)
    notes: str = ""

    @property
    def key(self) -> str:
        if self.leetcode_id:
            return f"id:{self.leetcode_id}"
        if self.url:
            return f"url:{self.url}"
        return f"title:{self.title.lower()}"

    def as_csv_row(self) -> dict[str, Any]:
        return {
            "leetcode_id": self.leetcode_id,
            "title": self.title,
            "slug": self.slug,
            "url": self.url,
            "description": self.description,
            "difficulty": self.difficulty,
            "publication_date": self.publication_date,
            "date_type": self.date_type,
            "original_date_field": self.original_date_field,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "extracted_at": self.extracted_at,
            "tags": "; ".join(self.tags),
            "constraints": self.constraints,
            "examples": self.examples,
            "signature": self.signature,
            "test_cases": self.test_cases,
            "reference_solution": self.reference_solution,
            "source_license": self.source_license,
            "completeness": self.completeness,
            "date_conflicts": "; ".join(self.date_conflicts),
            "notes": self.notes,
        }
