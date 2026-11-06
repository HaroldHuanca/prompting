from __future__ import annotations

import argparse
import json

from .pipeline import build_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect, normalize, filter, and export LeetCode problem records.")
    parser.add_argument("--output-dir", default="data", help="Directory where CSV/JSON files will be written.")
    parser.add_argument("--refresh", action="store_true", help="Force a fresh fetch instead of using cached records.")
    args = parser.parse_args()

    summary = build_dataset(output_dir=args.output_dir)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0
