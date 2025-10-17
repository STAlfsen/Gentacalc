import math

import pytest

from gentacalc.anthropometrics import WeightMetrics, compute_weight_metrics
from gentacalc.models import PatientInput


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


def test_weight_metrics_matches_excel_default(default_patient: PatientInput) -> None:
    metrics = compute_weight_metrics(default_patient)
    assert math.isclose(metrics.bmi or 0, 17.1562620356, rel_tol=1e-9)
    assert math.isclose(metrics.ideal_body_weight or 0, 60.8, rel_tol=1e-9)
    assert math.isclose(metrics.adjusted_body_weight or 0, 56.08, rel_tol=1e-9)
    assert metrics.dosing_weight == pytest.approx(49)


@pytest.mark.parametrize(
    "sex,height,weight,expected_ibw,expected_adj,expected_dosing",
    [
        ("male", 180, 140, 75.2, 101.12, 101.12),
        ("female", 160, 50, 52.7, 51.62, 50),
    ],
)
def test_dosing_weight_rules(sex, height, weight, expected_ibw, expected_adj, expected_dosing):
    patient = PatientInput(
        sex=sex,
        age_years=50,
        weight_kg=weight,
        height_cm=height,
        creatinine_umol_l=80,
        mg_per_kg=6,
        first_dose_hour=12,
    )
    metrics = compute_weight_metrics(patient)
    assert metrics.ideal_body_weight == pytest.approx(expected_ibw, rel=1e-4)
    assert metrics.adjusted_body_weight == pytest.approx(expected_adj, rel=1e-4)
    assert metrics.dosing_weight == pytest.approx(expected_dosing, rel=1e-4)
