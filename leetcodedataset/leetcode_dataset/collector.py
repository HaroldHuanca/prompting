from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, List
from urllib import error, request

import pyarrow.parquet as pq

from .models import ProblemRecord


OFFICIAL_LEETCODE_API = "https://leetcode.com/api/problems/all/"
HF_DATASET_PATH = Path(__file__).resolve().parents[1] / "hf_dataset" / "leetcode-solutions"


def _fetch_json(url: str) -> Any:
    with request.urlopen(url, timeout=20) as response:
        payload = response.read()
    return json.loads(payload.decode("utf-8"))


def _slug_to_url(slug: str) -> str:
    return f"https://leetcode.com/problems/{slug}/"


def _normalize_hf_date(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return datetime.fromisoformat(value).date().isoformat()
        except ValueError:
            return value
    if hasattr(value, "isoformat"):
        try:
            return value.date().isoformat()
        except AttributeError:
            return value.isoformat()[:10]
    return str(value)


def local_huggingface_problem_records(dataset_dir: str | Path | None = None) -> List[ProblemRecord]:
    dataset_path = Path(dataset_dir) if dataset_dir is not None else HF_DATASET_PATH
    parquet_path = dataset_path / "leetcode-solutions.parquet"
    if not parquet_path.exists():
        return []

    table = pq.read_table(parquet_path)
    rows = table.to_pylist()
    records: List[ProblemRecord] = []
    for row in rows:
        title = row.get("title") or ""
        task_id = row.get("task_id") or ""
        slug = task_id or "" if task_id else title.lower().replace(" ", "-")
        description = row.get("problem_description") or ""
        difficulty = row.get("difficulty") or "Unknown"
        estimated = _normalize_hf_date(row.get("estimated_date"))
        record = ProblemRecord(
            leetcode_id=str(row.get("parallel_id")) if row.get("parallel_id") is not None else None,
            title=title,
            slug=slug,
            url=_slug_to_url(slug) if slug else "https://leetcode.com/problemset/all/",
            description=description,
            difficulty=difficulty,
            publication_date=estimated,
            date_type="estimated" if estimated else "unknown",
            original_date_field="estimated_date",
            source_name="huggingface_tkeskin_leetcode_solutions",
            source_url="https://huggingface.co/datasets/tkeskin/leetcode-solutions",
            tags=[str(tag) for tag in (row.get("tags") or [])],
            constraints="",
            examples=json.dumps(row.get("input_output") or [], ensure_ascii=False),
            signature=row.get("entry_point") or "",
            test_cases=json.dumps(row.get("input_output") or [], ensure_ascii=False),
            reference_solution=row.get("python") or "",
            source_license="MIT + Apache 2.0",
            completeness="complete" if len((description or "").strip()) > 160 else "partial",
            notes="Downloaded from the Hugging Face dataset tkeskin/leetcode-solutions and mapped to the experimental problem schema.",
        )
        records.append(record)
    return records


def live_problem_records() -> List[ProblemRecord]:
    try:
        payload = _fetch_json(OFFICIAL_LEETCODE_API)
    except (ValueError, error.URLError, error.HTTPError):
        return []

    records: List[ProblemRecord] = []
    items = payload.get("stat_status_pairs", [])
    for item in items:
        stat = item.get("stat", {})
        question_id = stat.get("question_id")
        title = stat.get("question__title") or ""
        slug = stat.get("question__title_slug") or ""
        difficulty_rank = item.get("difficulty", {}).get("level")
        difficulty = {
            1: "Easy",
            2: "Medium",
            3: "Hard",
        }.get(difficulty_rank, "Unknown")

        record = ProblemRecord(
            leetcode_id=str(question_id) if question_id is not None else None,
            title=title,
            slug=slug,
            url=_slug_to_url(slug) if slug else "https://leetcode.com/problemset/all/",
            description="",
            difficulty=difficulty,
            publication_date=None,
            date_type="unknown",
            source_name="leetcode_api",
            source_url=OFFICIAL_LEETCODE_API,
            tags=[],
            notes="Retrieved from the public LeetCode problems API.",
        )
        records.append(record)
    return records


def fallback_problem_records() -> List[ProblemRecord]:
    sample = [
        {
            "leetcode_id": "4054",
            "title": "Longest Increasing Path in a Matrix",
            "slug": "longest-increasing-path-in-a-matrix",
            "description": "Given an m x n matrix, return the length of the longest increasing path.",
            "difficulty": "Hard",
            "publication_date": "2024-08-09",
            "date_type": "official",
            "source_name": "example_dataset",
            "source_url": "https://example.invalid/records/4054",
            "tags": ["Dynamic Programming", "Graph", "Topological Sort"],
            "constraints": "1 <= m, n <= 2000",
            "examples": "Input: grid = [[9,9,4],[6,6,8],[2,1,1]]\nOutput: 4",
            "signature": "class Solution:\n    def longestIncreasingPath(self, matrix: list[list[int]]) -> int:",
            "reference_solution": "Use memoized DFS with topological sorting semantics.",
        },
        {
            "leetcode_id": "4055",
            "title": "Minimum Cost to Connect Points",
            "slug": "min-cost-to-connect-points",
            "description": "Return the minimum cost to connect all points with a Steiner tree variant.",
            "difficulty": "Medium",
            "publication_date": "2024-08-15",
            "date_type": "official",
            "source_name": "example_dataset",
            "source_url": "https://example.invalid/records/4055",
            "tags": ["Graph", "Prim", "Union-Find"],
            "constraints": "2 <= points.length <= 1000",
            "examples": "Input: points = [[0,0],[2,2],[3,10],[5,2],[7,0]]\nOutput: 20",
            "signature": "class Solution:\n    def minCostConnectPoints(self, points: list[list[int]]) -> int:",
        },
        {
            "leetcode_id": "4056",
            "title": "Count Paths Through Grid",
            "slug": "count-paths-through-grid",
            "description": "Count the number of valid paths through a grid with obstacle constraints.",
            "difficulty": "Easy",
            "publication_date": "2024-08-27",
            "date_type": "official",
            "source_name": "example_dataset",
            "source_url": "https://example.invalid/records/4056",
            "tags": ["Dynamic Programming", "Grid"],
            "constraints": "1 <= m, n <= 100",
            "examples": "Input: grid = [[0,0],[0,0]]\nOutput: 2",
            "signature": "class Solution:\n    def countPaths(self, grid: list[list[int]]) -> int:",
        },
        {
            "leetcode_id": "4057",
            "title": "Find the Longest Balanced Subsequence",
            "slug": "find-the-longest-balanced-subsequence",
            "description": "Find the longest sub-sequence whose counts of opening and closing brackets stay balanced.",
            "difficulty": "Medium",
            "publication_date": "2024-08-15",
            "date_type": "estimated",
            "source_name": "example_dataset",
            "source_url": "https://example.invalid/records/4057",
            "tags": ["String", "Greedy"],
            "constraints": "1 <= s.length <= 10^5",
            "examples": "Input: s = \"(()())\"\nOutput: 6",
            "signature": "class Solution:\n    def longestBalancedSubsequence(self, s: str) -> int:",
        },
        {
            "leetcode_id": "4058",
            "title": "Best Time to Buy and Sell After Events",
            "slug": "best-time-to-buy-and-sell-after-events",
            "description": "A dynamic programming problem on event-driven stock price updates.",
            "difficulty": "Hard",
            "publication_date": "2024-09-01",
            "date_type": "unknown",
            "source_name": "example_dataset",
            "source_url": "https://example.invalid/records/4058",
            "tags": ["Dynamic Programming", "Stock Market"],
            "constraints": "1 <= events.length <= 10^5",
            "examples": "Input: events = [1,2,3]\nOutput: 6",
            "signature": "class Solution:\n    def maxProfit(self, events: list[int]) -> int:",
        },
        {
            "leetcode_id": "101",
            "title": "Symmetric Tree",
            "slug": "symmetric-tree",
            "description": "Check whether a binary tree is symmetric.",
            "difficulty": "Easy",
            "publication_date": "2019-08-12",
            "date_type": "official",
            "source_name": "example_dataset",
            "source_url": "https://example.invalid/records/101",
            "tags": ["Tree", "Recursion"],
            "constraints": "The number of nodes in the tree is in the range [1, 1000].",
            "examples": "Input: root = [1,2,2,3,4,4,3]\nOutput: true",
            "signature": "class Solution:\n    def isSymmetric(self, root: Optional[TreeNode]) -> bool:",
        },
        {
            "leetcode_id": "4059",
            "title": "Minimize Maximum Difference",
            "slug": "minimize-maximum-difference",
            "description": "Minimize the maximum difference under a set of constraints.",
            "difficulty": "Medium",
            "publication_date": "2024-08-06",
            "date_type": "official",
            "source_name": "example_dataset",
            "source_url": "https://example.invalid/records/4059",
            "tags": ["Binary Search", "Arrays"],
            "constraints": "1 <= nums.length <= 10^5",
            "examples": "Input: nums = [1,5,6,14]\nOutput: 4",
            "signature": "class Solution:\n    def minimizeMax(self, nums: list[int]) -> int:",
        },
    ]

    records = []
    for item in sample:
        rec = ProblemRecord(
            leetcode_id=item["leetcode_id"],
            title=item["title"],
            slug=item["slug"],
            url=_slug_to_url(item["slug"]),
            description=item.get("description", ""),
            difficulty=item.get("difficulty", "Unknown"),
            publication_date=item.get("publication_date"),
            date_type=item.get("date_type", "unknown"),
            source_name=item.get("source_name", "example_dataset"),
            source_url=item.get("source_url", _slug_to_url(item["slug"])),
            tags=item.get("tags", []),
            constraints=item.get("constraints", ""),
            examples=item.get("examples", ""),
            signature=item.get("signature", ""),
            test_cases=item.get("test_cases", ""),
            reference_solution=item.get("reference_solution", ""),
            notes=item.get("notes", "Fallback sample dataset used when live sources are inaccessible."),
        )
        records.append(rec)
    return records


def collect_problem_records() -> List[ProblemRecord]:
    records = local_huggingface_problem_records()
    if records:
        return records
    records = live_problem_records()
    if records:
        return records
    return fallback_problem_records()


class ProblemCollector:
    def collect(self) -> List[ProblemRecord]:
        return collect_problem_records()
