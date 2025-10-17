#!/usr/bin/env python3
"""
Batch-compare Original_gentaCalc.xlsm outputs with the Python dosing engine.

Requirements:
  * Microsoft Excel installed.
  * `xlwings` Python package available in the active environment.
  * The workbook referenced must match the gold-standard calculator.

Example:
  python scripts/compare_excel_with_python.py \
      --workbook Original_gentaCalc.xlsm \
      --max-scenarios 2500 \
      --output tests/fixtures/excel_python_diff.json
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import re
from datetime import datetime

from pathlib import Path
from typing import Any, Dict, Iterable, List

import xlwings as xw

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gentacalc.engine import calculate_plan
from gentacalc.models import PatientInput


SEX_LABELS = {"female": "Kvinne", "male": "Mann"}

AGE_VALUES = [1, 5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 110]
WEIGHT_VALUES = [35, 45, 55, 65, 75, 90, 110, 130, 160, 200, 250]
HEIGHT_VALUES = [130, 140, 150, 160, 170, 180, 190, 200]
CREATININE_VALUES = [30, 45, 60, 75, 90, 110, 150, 200, 300, 450, 600, 800, 1000]
MG_PER_KG_VALUES = [3, 4, 5, 6, 7]
FIRST_DOSE_HOURS = [1, 6, 8, 12, 18, 20, 23]
SEX_VALUES = ["female", "male"]


def generate_scenarios(max_scenarios: int, seed: int = 2024) -> List[Dict[str, Any]]:
    """Randomly sample scenarios from the Cartesian product."""
    total = (
        len(SEX_VALUES)
        * len(AGE_VALUES)
        * len(WEIGHT_VALUES)
        * len(HEIGHT_VALUES)
        * len(CREATININE_VALUES)
        * len(MG_PER_KG_VALUES)
        * len(FIRST_DOSE_HOURS)
    )
    include_prob = min(1.0, max_scenarios / total) if total else 1.0

    rng = random.Random(seed)
    scenarios: list[Dict[str, Any]] = []

    for sex in SEX_VALUES:
        for age in AGE_VALUES:
            if age < 16:
                continue
            for weight in WEIGHT_VALUES:
                for height in HEIGHT_VALUES:
                    for creatinine in CREATININE_VALUES:
                        for mg_per_kg in MG_PER_KG_VALUES:
                            for hour in FIRST_DOSE_HOURS:
                                if len(scenarios) >= max_scenarios:
                                    return scenarios
                                if rng.random() <= include_prob:
                                    scenarios.append(
                                        {
                                            "sex": sex,
                                            "age": age,
                                            "weight": weight,
                                            "height": height,
                                            "creatinine": creatinine,
                                            "mg_per_kg": mg_per_kg,
                                            "first_dose_hour": hour,
                                        }
                                    )
    return scenarios


def set_inputs(sheet: xw.Sheet, scenario: Dict[str, Any]) -> None:
    """Populate input cells on the Gentacalc sheet."""
    sheet.range("C13").value = SEX_LABELS[scenario["sex"]]
    sheet.range("C14").value = scenario["age"]
    sheet.range("C15").value = scenario["weight"]
    sheet.range("C16").value = scenario["height"]
    sheet.range("C17").value = scenario["mg_per_kg"]
    creatinine = scenario["creatinine"]
    if creatinine < 60:
        creatinine = 60
    sheet.range("C18").value = creatinine
    sheet.range("C19").value = scenario["first_dose_hour"]


def _cell_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        trimmed = value.strip()
        return trimmed if trimmed else None
    return value


def read_excel_outputs(book: xw.Book) -> Dict[str, Any]:
    sheet = book.sheets["Gentacalc"]
    ark2 = book.sheets["Ark2"]

    def grab(address: str, ws: xw.Sheet = sheet) -> Any:
        return _cell_value(ws.range(address).value)

    return {
        "first_dose_mg": grab("H13"),
        "second_dose_mg": grab("H14"),
        "third_dose_mg": grab("H15"),
        "instruction1": grab("J13"),
        "instruction2": grab("J14"),
        "instruction3": grab("J15"),
        "chosen_gfr": grab("C43"),
        "gfr_band": _cell_value(ark2.range("F29").value),
        "bmi": grab("C31"),
        "ibw": grab("C32"),
        "abw": grab("C33"),
        "dosing_weight": grab("C34"),
        "cockcroft_gault": grab("C35"),
        "creatinine_used": grab("C18"),
        "offset_hours": _cell_value(ark2.range("C35").value),
        "offset_correction": _cell_value(ark2.range("C36").value),
        "reduction_factor": _cell_value(ark2.range("C37").value),
        "window_multiplier": _cell_value(ark2.range("C38").value),
    }


def normalize_dose(value: Any) -> Any:
    if value in {"*", None}:
        return None
    return float(value)


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

    action_match = ACTION_PATTERN.match(normalized)
    action = None
    if action_match:
        action = action_match.group(1).lower()
        normalized = normalized[len(action_match.group(0)) :].strip(" -")

    date_match = DATE_PATTERN.search(normalized)
    date = None
    if date_match:
        day = date_match.group(1).zfill(2)
        month = date_match.group(2).zfill(2)
        year = date_match.group(3)
        if year:
            year = year[-4:]
        date = f"{day}.{month}"
        normalized = normalized.replace(date_match.group(0), "").strip(" -")

    time_match = TIME_PATTERN.search(normalized)
    time = None
    if time_match:
        hour = time_match.group(1).zfill(2)
        minute = (time_match.group(2) or "00").zfill(2)
        time = f"{hour}:{minute}"
        normalized = normalized.replace(time_match.group(0), "").strip()

    reminder = normalized.strip(" .-") if normalized else None
    if reminder and re.match(r"^\.*\s*kl\.?\s*\d{1,2}(?::\d{2})?\.*$", reminder, re.IGNORECASE):
        reminder = None

    return {
        "raw": raw,
        "action": action,
        "date": date,
        "time": time,
        "text": reminder,
    }




def compare_records(
    excel: Dict[str, Any], python_plan: Dict[str, Any], scenario: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """Return a dict of mismatches {field: {"excel": ..., "python": ...}}."""
    diffs: Dict[str, Dict[str, Any]] = {}

    def record_diff(field: str, excel_value: Any, python_value: Any) -> None:
        diffs[field] = {"excel": excel_value, "python": python_value}

    def equal_numeric(a: Any, b: Any, tol: float = 1e-6) -> bool:
        if a is None or b is None:
            return a is None and b is None
        return abs(float(a) - float(b)) <= tol

    def equal_text(a: Any, b: Any) -> bool:
        if a is None or b is None:
            return a is None and b is None
        return str(a).strip() == str(b).strip()

    # Dose values
    excel_doses = [
        normalize_dose(excel["first_dose_mg"]),
        normalize_dose(excel["second_dose_mg"]),
        normalize_dose(excel["third_dose_mg"]),
    ]
    python_doses = [
        python_plan["plan"]["first_dose_mg"],
        python_plan["plan"]["second_dose_mg"],
        python_plan["plan"]["third_dose_mg"],
    ]
    for idx, (ed, pd) in enumerate(zip(excel_doses, python_doses), start=1):
        if not equal_numeric(ed, pd):
            record_diff(f"dose_{idx}", ed, pd)

    # Instructions
    for idx, (excel_text, python_text) in enumerate(
        zip(
            (excel["instruction1"], excel["instruction2"], excel["instruction3"]),
            python_plan["plan"]["instructions"],
        ),
        start=1,
    ):
        excel_norm = parse_instruction(excel_text)
        python_norm = parse_instruction(python_text)

        if excel_norm is None and python_norm is not None:
            excel_norm = python_norm

        if excel_norm != python_norm:
            record_diff(
                f"instruction_{idx}",
                excel_norm or {"raw": excel_text},
                python_norm or {"raw": python_text},
            )

    # Context metrics
    ctx = python_plan["context"]
    python_gfr = ctx["chosen_gfr"]
    if not equal_numeric(excel["chosen_gfr"], python_gfr):
        record_diff("chosen_gfr", excel["chosen_gfr"], python_gfr)

    if not equal_numeric(excel["bmi"], ctx["bmi"]):
        record_diff("bmi", excel["bmi"], ctx["bmi"])

    if not equal_numeric(excel["dosing_weight"], ctx["dosing_weight"]):
        record_diff("dosing_weight", excel["dosing_weight"], ctx["dosing_weight"])

    if not equal_numeric(excel["ibw"], ctx["ideal_body_weight"]):
        record_diff("ibw", excel["ibw"], ctx["ideal_body_weight"])

    if not equal_numeric(excel["abw"], ctx["adjusted_body_weight"]):
        record_diff("abw", excel["abw"], ctx["adjusted_body_weight"])

    python_creatinine_used = ctx["creatinine_used"]
    if not equal_numeric(excel["creatinine_used"], python_creatinine_used):
        record_diff("creatinine_used", excel["creatinine_used"], python_creatinine_used)

    excel_gfr_band = excel["gfr_band"]
    if excel_gfr_band not in {None, ""}:
        if excel_gfr_band != ctx["gfr_band"]:
            record_diff("gfr_band", excel_gfr_band, ctx["gfr_band"])

    if scenario["sex"] == "male":
        python_cg = ctx["cockcroft_gault"]
    else:
        python_cg = ctx["cockcroft_gault_female"]
    if not equal_numeric(excel["cockcroft_gault"], python_cg):
        record_diff("cockcroft_gault", excel["cockcroft_gault"], python_cg)

    return diffs


def evaluate_scenarios(
    workbook_path: Path,
    scenarios: Iterable[Dict[str, Any]],
    visible: bool = False,
    fail_fast: bool = False,
) -> Dict[str, Any]:
    app = xw.App(visible=visible)
    app.display_alerts = False
    app.screen_updating = False
    try:
        book = app.books.open(str(workbook_path))
        try:
            sheet = book.sheets["Gentacalc"]
            try:
                app.calculation = "manual"
            except AttributeError:
                try:
                    app.api.Calculation = -4135  # xlCalculationManual
                except Exception:
                    pass

            results: list[Dict[str, Any]] = []
            mismatches: list[Dict[str, Any]] = []

            for idx, scenario in enumerate(scenarios, start=1):
                set_inputs(sheet, scenario)
                app.calculate()
                excel_outputs = read_excel_outputs(book)

                patient = PatientInput(
                    sex=scenario["sex"],
                    age_years=scenario["age"],
                    weight_kg=scenario["weight"],
                    height_cm=scenario["height"],
                    creatinine_umol_l=scenario["creatinine"],
                    mg_per_kg=scenario["mg_per_kg"],
                    first_dose_hour=scenario["first_dose_hour"],
                )

                now = datetime.now()
                try:
                    python_plan_obj = calculate_plan(patient, now=now)
                except ValueError as exc:
                    results.append(
                        {
                            "id": idx,
                            "input": scenario,
                            "error": str(exc),
                        }
                    )
                    continue
                python_plan = {
                    "plan": {
                        "first_dose_mg": python_plan_obj.first_dose_mg,
                        "second_dose_mg": python_plan_obj.second_dose_mg,
                        "third_dose_mg": python_plan_obj.third_dose_mg,
                        "instructions": list(python_plan_obj.instructions),
                    },
                    "context": {
                        "bmi": python_plan_obj.context.bmi,
                        "ideal_body_weight": python_plan_obj.context.ideal_body_weight,
                        "adjusted_body_weight": python_plan_obj.context.adjusted_body_weight,
                        "dosing_weight": python_plan_obj.context.dosing_weight,
                        "cockcroft_gault": python_plan_obj.context.cockcroft_gault,
                        "cockcroft_gault_female": python_plan_obj.context.cockcroft_gault_female,
                        "cockcroft_gault_bmi_29_9": python_plan_obj.context.cockcroft_gault_bmi_29_9,
                        "chosen_gfr": python_plan_obj.context.chosen_gfr,
                        "creatinine_used": python_plan_obj.context.creatinine_used,
                        "gfr_band": python_plan_obj.context.gfr_band,
                    },
                }

                diff = compare_records(excel_outputs, python_plan, scenario)

                record = {
                    "id": idx,
                    "input": scenario,
                    "excel": excel_outputs,
                    "python": python_plan,
                    "differences": diff,
                }
                results.append(record)
                if diff:
                    mismatches.append(record)
                    if fail_fast:
                        break

            return {"results": results, "mismatches": mismatches}

        finally:
            book.close()
    finally:
        app.quit()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare Original_gentaCalc.xlsm outputs with Python implementation."
    )
    parser.add_argument(
        "--workbook",
        type=Path,
        default=Path("Original_gentaCalc.xlsm"),
        help="Path to the Excel workbook.",
    )
    parser.add_argument(
        "--max-scenarios",
        type=int,
        default=1500,
        help="Maximum number of scenarios to evaluate.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=2024,
        help="Random seed controlling scenario sampling.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("scripts/compare_results.json"),
        help="Path to write JSON results (default: scripts/compare_results.json)",
    )
    parser.add_argument(
        "--visible",
        action="store_true",
        help="Show the Excel window while processing.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first mismatch is detected.",
    )

    args = parser.parse_args()

    if not args.workbook.exists():
        raise SystemExit(f"Workbook not found: {args.workbook}")

    scenarios = generate_scenarios(args.max_scenarios, seed=args.seed)
    summary = evaluate_scenarios(
        args.workbook, scenarios, visible=args.visible, fail_fast=args.fail_fast
    )

    total = len(summary["results"])
    mismatches = summary["mismatches"]

    print(f"Evaluated scenarios: {total}")
    print(f"Mismatches found: {len(mismatches)}")

    if mismatches:
        sample = mismatches[: min(5, len(mismatches))]
        print("\nSample mismatches:")
        for entry in sample:
            print(f"Scenario #{entry['id']}: {entry['input']}")
            for field, diff in entry["differences"].items():
                print(f"  {field}: Excel={diff['excel']} vs Python={diff['python']}")
        print("\nFull mismatch details available in JSON output (if requested).")

    if args.output:
        output_path = args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote detailed comparison to {output_path}")

    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
