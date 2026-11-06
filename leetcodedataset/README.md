# LeetCode Dataset Builder

This project builds a filtered LeetCode problem dataset suitable for experimental work on prompt engineering.

## Local Hugging Face dataset

The project now prefers a local copy of the Hugging Face dataset:

- `hf_dataset/leetcode-solutions/`

This folder is downloaded from `tkeskin/leetcode-solutions` and includes problem metadata, descriptions, tags, difficulty, and estimated dates for research workflows.

## Usage

```bash
python main.py --output-dir data
```

The script collects problem metadata from the local Hugging Face dataset when available, then falls back to the public LeetCode API, and finally a static sample dataset if needed. It normalizes, deduplicates, filters by the reference date 2024-08-06, and writes CSV/JSON exports to the configured directory.

## Outputs

- `data/problems_normalized.csv`
- `data/problems_after_reference.csv`
- `data/problems_after_reference_estimated.csv`
- `data/problems_without_verified_date.csv`

The local Hugging Face dataset is stored under `hf_dataset/leetcode-solutions/` and is not overwritten by the project.
