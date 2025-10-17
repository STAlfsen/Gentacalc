import json
from pathlib import Path
from datetime import datetime

import pytest

from gentacalc.engine import calculate_plan
from gentacalc.models import PatientInput


def test_engine_matches_excel_snapshot_default_case():
    snapshot = json.loads(Path("tests/fixtures/default_snapshot.json").read_text())
    now = datetime(2025, 8, 24, 9, 0)

    patient = PatientInput(
        sex="female",
        age_years=snapshot["Gentacalc"]["C14"],
        weight_kg=snapshot["Gentacalc"]["C15"],
        height_cm=snapshot["Gentacalc"]["C16"],
        creatinine_umol_l=snapshot["Gentacalc"]["C18"],
        mg_per_kg=snapshot["Gentacalc"]["C17"],
        first_dose_hour=snapshot["Gentacalc"]["C19"],
    )

    plan = calculate_plan(patient, now=now)
    assert plan.first_dose_mg == snapshot["Gentacalc"]["H13"]
    assert plan.second_dose_mg == snapshot["Gentacalc"]["H14"]
    assert plan.third_dose_mg is None
    assert plan.instructions[0] == snapshot["Gentacalc"]["J13"]
    assert plan.instructions[1] == snapshot["Gentacalc"]["J14"]
    assert plan.instructions[2] == snapshot["Gentacalc"]["J15"]
    assert plan.context.gfr_band == snapshot["Ark2"]["F29"]
    assert plan.context.chosen_gfr == snapshot["Gentacalc"]["C21"]
    assert plan.monitoring.startswith("Vurder videre bruk")


def test_engine_rejects_patients_younger_than_16():
    patient = PatientInput(
        sex="female",
        age_years=15,
        weight_kg=50,
        height_cm=160,
        creatinine_umol_l=70,
        mg_per_kg=5,
        first_dose_hour=12,
    )

    with pytest.raises(ValueError, match="under 16"):
        calculate_plan(patient)


def test_monitoring_recommendation_gfr_over_60():
    patient = PatientInput(
        sex="male",
        age_years=45,
        weight_kg=80,
        height_cm=180,
        creatinine_umol_l=70,
        mg_per_kg=7,
        first_dose_hour=20,
    )
    plan = calculate_plan(patient, now=datetime(2025, 8, 24, 9, 0))
    assert "27.08 08:00" in plan.monitoring


def test_monitoring_recommendation_gfr_between_40_and_60():
    patient = PatientInput(
        sex="female",
        age_years=70,
        weight_kg=60,
        height_cm=165,
        creatinine_umol_l=100,
        mg_per_kg=5,
        first_dose_hour=10,
    )
    plan = calculate_plan(patient, now=datetime(2025, 8, 24, 9, 0))
    assert "26.08 08:00" in plan.monitoring
