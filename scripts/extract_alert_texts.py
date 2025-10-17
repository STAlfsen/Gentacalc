#!/usr/bin/env python3
"""Extracts alert textbox content from the Excel gold standard."""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


TARGET_SHAPES = {
    "erik": "under_80_guidance",
    "åtti": "over_80_guidance",
    "BMI": "bmi_over_35",
    "BMIm": "bmi_30_35",
    "Dose": "dose_over_600",
    "Kreatinin": "creatinine_floor",
    "Alder": "over_80_precautions",
    "TekstSylinder 4": "contraindications",
    "TekstSylinder 8": "relative_contraindications",
    "TekstSylinder 9": "habituell_creatinine",
}


def extract(path: Path) -> dict[str, list[str]]:
    with zipfile.ZipFile(path) as zf:
        xml = ET.fromstring(zf.read("xl/drawings/drawing1.xml"))

    ns = {
        "xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
        "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    }

    payload: dict[str, list[str]] = {}
    for sp in xml.findall(".//xdr:sp", ns):
        name = sp.find("xdr:nvSpPr/xdr:cNvPr", ns).get("name")
        if name not in TARGET_SHAPES:
            continue
        texts: list[str] = []
        for paragraph in sp.findall(".//a:p", ns):
            parts = [t.text or "" for t in paragraph.findall(".//a:t", ns)]
            combined = "".join(parts).strip()
            if combined:
                texts.append(combined)
        payload[TARGET_SHAPES[name]] = texts
    return payload


def main() -> None:
    try:
        workbook = Path(sys.argv[1])
    except IndexError as exc:  # pragma: no cover - CLI guard
        raise SystemExit("Usage: extract_alert_texts.py <path-to-xlsm>") from exc

    if not workbook.exists():
        raise SystemExit(f"Workbook not found: {workbook}")

    data = extract(workbook)
    out_dir = Path(__file__).resolve().parents[1] / "gentacalc" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "alert_texts.json"
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {out_path.relative_to(Path.cwd())}")


if __name__ == "__main__":  # pragma: no cover
    main()
