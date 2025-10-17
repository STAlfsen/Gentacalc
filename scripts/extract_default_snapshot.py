#!/usr/bin/env python3
"""Capture reference outputs from the original Excel workbook."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from openpyxl import load_workbook

CELL_GROUPS = {
    "Gentacalc": [
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C18",
        "C19",
        "C21",
        "C22",
        "C31",
        "C32",
        "C33",
        "C34",
        "C35",
        "C42",
        "C43",
        "H13",
        "H14",
        "H15",
        "J13",
        "J14",
        "J15",
    ],
    "Ark2": [
        "F29",
        "F43",
        "F44",
        "F45",
        "G43",
        "G44",
        "G45",
    ],
}


def extract(workbook_path: Path) -> dict[str, dict[str, float | str | None]]:
    wb = load_workbook(workbook_path, keep_vba=True, data_only=True)
    output: dict[str, dict[str, float | str | None]] = {}
    for sheet_name, cells in CELL_GROUPS.items():
        sheet = wb[sheet_name]
        output[sheet_name] = {cell: sheet[cell].value for cell in cells}
    return output


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: extract_default_snapshot.py <path-to-xlsm>")
    workbook_path = Path(sys.argv[1])
    if not workbook_path.exists():
        raise SystemExit(f"Workbook not found: {workbook_path}")

    snapshot = extract(workbook_path)
    out_dir = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "default_snapshot.json"
    out_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {out_path.relative_to(Path.cwd())}")


if __name__ == "__main__":  # pragma: no cover
    main()
