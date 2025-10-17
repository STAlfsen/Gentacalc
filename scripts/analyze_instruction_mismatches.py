#!/usr/bin/env python3
"""Extract instruction mismatches from compare_results.json."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

WEEKDAY_PATTERN = re.compile(
    r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
    re.IGNORECASE,
)
TIME_PATTERN = re.compile(r"kl\.?\s*(\d{1,2})[:\.]?\s*(\d{2})?", re.IGNORECASE)
DATE_PATTERN = re.compile(r"(\d{1,2})\.(\d{1,2})(?:\.(\d{2,4}))?")
ACTION_PATTERN = re.compile(
    r"^(gis umiddelbart|gis 36 timer etter dose 1|gis|bestill|tredje dose gentamicin skal ikke gis)",
    re.IGNORECASE,
)
TRAILING_TIME_PATTERN = re.compile(r"^\.*\s*kl\.?\s*\d{1,2}(?::\d{2})?\.*$", re.IGNORECASE)


def parse_instruction(text: Any) -> Optional[Dict[str, Optional[str]]]:
    if text is None:
        return None
    raw = str(text).strip()
    if not raw:
        return None

    normalized = re.sub(r"\s+", " ", raw)
    normalized = WEEKDAY_PATTERN.sub("", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    normalized = re.sub(r"\.\s*(?=kl)", " ", normalized, flags=re.IGNORECASE)

    action = None
    match = ACTION_PATTERN.match(normalized)
    if match:
        action = match.group(1).lower()
        normalized = normalized[len(match.group(0)) :].strip(" -")

    year = None
    date = None
    match = DATE_PATTERN.search(normalized)
    if match:
        day = match.group(1).zfill(2)
        month = match.group(2).zfill(2)
        year = match.group(3)
        if year:
            year = year[-4:]
        date = f"{day}.{month}"
        normalized = normalized.replace(match.group(0), "").strip(" -")

    time = None
    match = TIME_PATTERN.search(normalized)
    if match:
        hour = match.group(1).zfill(2)
        minute = (match.group(2) or "00").zfill(2)
        time = f"{hour}:{minute}"
        normalized = normalized.replace(match.group(0), "").strip()

    reminder = normalized.strip(" .-") if normalized else None
    if reminder and TRAILING_TIME_PATTERN.match(reminder):
        reminder = None

    return {
        "raw": raw,
        "action": action,
        "date": date,
        "time": time,
        "text": reminder,
    }


def load_results(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("results", data)


def normalize_entry(entry: Any) -> Optional[Dict[str, Optional[str]]]:
    if entry is None:
        return None

    def standardize(payload: Optional[Dict[str, Optional[str]]]) -> Optional[Dict[str, Optional[str]]]:
        if not payload:
            return None
        result = dict(payload)
        date = result.get("date")
        if date:
            parts = date.split(".")
            if len(parts) >= 2:
                result["date"] = f"{parts[0].zfill(2)}.{parts[1].zfill(2)}"
        text_value = result.get("text")
        if text_value and TRAILING_TIME_PATTERN.match(text_value):
            result["text"] = None
        return result

    if isinstance(entry, dict):
        if {"action", "date", "time", "text"}.issubset(entry.keys()):
            return standardize(entry)
        if "raw" in entry:
            return standardize(parse_instruction(entry["raw"]))
        if "normalized" in entry:
            source = entry.get("raw") or entry.get("excel") or entry.get("python")
            return standardize(parse_instruction(source))
    return standardize(parse_instruction(entry))



def main() -> None:
    parser = argparse.ArgumentParser(description="List instruction mismatches")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("scripts/compare_results.json"),
        help="Path to comparison JSON (default: scripts/compare_results.json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write mismatches as JSON",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Comparison file not found: {args.input}")

    results = load_results(args.input)

    mismatches: List[Dict[str, Any]] = []
    for entry in results:
        diffs = entry.get("differences", {})
        inst = {}
        for key, value in diffs.items():
            if not key.startswith("instruction_"):
                continue
            if isinstance(value, dict) and "excel" in value and "python" in value:
                excel_part = normalize_entry(value["excel"])
                python_part = normalize_entry(value["python"])
            else:
                excel_part = normalize_entry(value)
                python_part = normalize_entry(value)

            excel_cmp = {k: v for k, v in (excel_part or {}).items() if k != "raw"}
            python_cmp = {k: v for k, v in (python_part or {}).items() if k != "raw"}
            if excel_cmp == python_cmp:
                continue
            inst[key] = {
                "excel": excel_part,
                "python": python_part,
            }
        if inst:
            mismatches.append(
                {
                    "id": entry.get("id"),
                    "input": entry.get("input"),
                    "instructions": inst,
                }
            )

    print(f"Instruction mismatches: {len(mismatches)}")
    for sample in mismatches[:10]:
        print(f"- Scenario #{sample['id']}: {sample['input']}")
        for key, info in sample["instructions"].items():
            print(
                f"    {key}: Excel={info['excel']} vs Python={info['python']}"
            )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(mismatches, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"\nDetailed mismatches written to {args.output}")


if __name__ == "__main__":
    main()
