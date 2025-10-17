import math

import pytest

from gentacalc.anthropometrics import compute_weight_metrics
from gentacalc.models import PatientInput
from gentacalc.renal import compute_renal_metrics


@pytest.fixture
def default_patient() -> PatientInput:
    return PatientInput(
        sex="female",
        age_years=72,
        weight_kg=49,
        height_cm=169,
        creatinine_umol_l=77,
        mg_per_kg=6,
        first_dose_hour=23,
    )


def test_renal_metrics_matches_excel_default(default_patient: PatientInput):
    weight = compute_weight_metrics(default_patient)
    renal = compute_renal_metrics(default_patient, weight)

    assert renal.creatinine_used == 77
    assert renal.gfr_band == 2
    assert renal.chosen_gfr == 45
    assert math.isclose(renal.cockcroft_gault_female or 0, 45, rel_tol=1e-9)
    assert math.isclose(renal.cockcroft_gault_bmi_29_9 or 0, 78.7512, rel_tol=1e-4)


def test_creatinine_floor_applied_when_below_threshold():
    patient = PatientInput(
        sex="male",
        age_years=60,
        weight_kg=80,
        height_cm=175,
        creatinine_umol_l=45,  # below 60, should clamp
        mg_per_kg=6,
        first_dose_hour=10,
    )
    weight = compute_weight_metrics(patient)
    renal = compute_renal_metrics(patient, weight)
    assert renal.creatinine_used == 60
    assert renal.cockcroft_gault_male is not None
    assert renal.cockcroft_gault_male <  ( (140-60)*80)/(0.814*45)  # clamped reduces GFR


def test_high_bmi_uses_adjusted_weight_and_surrogate_gfr():
    patient = PatientInput(
        sex="male",
        age_years=50,
        weight_kg=140,
        height_cm=180,
        creatinine_umol_l=100,
        mg_per_kg=6,
        first_dose_hour=12,
    )
    weight = compute_weight_metrics(patient)
    renal = compute_renal_metrics(patient, weight)

    assert math.isclose(weight.dosing_weight, 101.12, rel_tol=1e-4)
    assert math.isclose(renal.cockcroft_gault_male or 0, 111, rel_tol=1e-9)
    assert math.isclose(renal.cockcroft_gault_bmi_29_9 or 0, 107.1, rel_tol=1e-3)
    assert renal.chosen_gfr == 111
    assert renal.gfr_band == 3
