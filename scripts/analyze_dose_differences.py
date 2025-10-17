#!/usr/bin/env python3
"""
Inspect comparison results and focus on dose discrepancies.

Usage:
    python scripts/analyze_dose_differences.py \
        --input scripts/compare_results.json \
        --output scripts/dose_mismatches.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


DOSE_KEYS = {"dose_1", "dose_2", "dose_3"}


def load_results(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "results" not in data or "mismatches" not in data:
        raise ValueError("Invalid comparison file: missing 'results' or 'mismatches'.")
    return data


def extract_dose_mismatches(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    mismatches = []
    for entry in data.get("results", []):
        inputs = entry.get("input") or {}
        if inputs.get("age", 0) < 16:
            continue
        python_plan = entry.get("python") or {}
        if "plan" not in python_plan:
            continue

        diff = entry.get("differences", {})
        dose_fields = {k: v for k, v in diff.items() if k in DOSE_KEYS}
        if dose_fields:
            excel_plan = entry.get("excel", {})
            mismatches.append(
                {
                    "id": entry.get("id"),
                    "input": inputs,
                    "dose_differences": dose_fields,
                    "excel_doses": {
                        "dose_1": excel_plan.get("first_dose_mg"),
                        "dose_2": excel_plan.get("second_dose_mg"),
                        "dose_3": excel_plan.get("third_dose_mg"),
                    },
                    "python_doses": {
                        "dose_1": python_plan["plan"].get("first_dose_mg"),
                        "dose_2": python_plan["plan"].get("second_dose_mg"),
                        "dose_3": python_plan["plan"].get("third_dose_mg"),
                    },
                }
            )
    return mismatches


def summarize(mismatches: List[Dict[str, Any]]) -> None:
    print(f"Dose mismatches: {len(mismatches)}")
    if not mismatches:
        return
    sample = mismatches[: min(len(mismatches), 10)]
    print("\nSample dose differences (up to 10 shown):")
    for entry in sample:
        scenario = entry["input"]
        print(f"- Scenario #{entry['id']}: {scenario}")
        for field, values in entry["dose_differences"].items():
            print(f"    {field}: Excel={values['excel']} vs Python={values['python']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract dose mismatches from comparison results.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("scripts/compare_results.json"),
        help="Path to comparison JSON (default: scripts/compare_results.json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write filtered mismatch data.",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Comparison file not found: {args.input}")

    data = load_results(args.input)
    mismatches = extract_dose_mismatches(data)
    summarize(mismatches)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(mismatches, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\nDetailed dose mismatches written to {args.output}")


if __name__ == "__main__":
    main()
