from datetime import datetime

import pytest

from gentacalc.anthropometrics import compute_weight_metrics
from gentacalc.dosing import compute_doses
from gentacalc.models import PatientInput
from gentacalc.renal import compute_renal_metrics


@pytest.fixture
def reference_now() -> datetime:
    return datetime(2025, 8, 24, 9, 0)


def test_dosing_plan_for_reference_patient(reference_now: datetime):
    patient = PatientInput(
        sex="female",
        age_years=72,
        weight_kg=49,
        height_cm=169,
        creatinine_umol_l=77,
        mg_per_kg=6,
        first_dose_hour=23,
    )
    weight = compute_weight_metrics(patient)
    renal = compute_renal_metrics(patient, weight)
    result = compute_doses(patient, weight, renal, now=reference_now)

    assert result.first_dose_mg == 280
    assert result.second_dose_mg == 280
    assert result.third_dose_mg is None
    assert result.instructions[0] == " Gis umiddelbart  -  24.08 23:00"
    assert (
        result.instructions[1]
        == " Gis 36 timer etter dose 1  -  26.08 11:00"
    )
    assert result.instructions[2] == " Tredje dose Gentamicin skal ikke gis"


def test_no_dosing_when_gfr_below_40(reference_now: datetime):
    patient = PatientInput(
        sex="male",
        age_years=78,
        weight_kg=70,
        height_cm=170,
        creatinine_umol_l=180,
        mg_per_kg=5,
        first_dose_hour=18,
    )
    weight = compute_weight_metrics(patient)
    renal = compute_renal_metrics(patient, weight)
    assert renal.gfr_band == 1
    result = compute_doses(patient, weight, renal, now=reference_now)
    assert result.first_dose_mg is None
    assert result.second_dose_mg is None
    assert result.third_dose_mg is None
    assert all(msg == " Gentamicin anbefales ikke ved GFR <40.  " for msg in result.instructions)


def test_high_gfr_dosing_schedule_with_reduction(reference_now: datetime):
    patient = PatientInput(
        sex="male",
        age_years=40,
        weight_kg=85,
        height_cm=180,
        creatinine_umol_l=60,
        mg_per_kg=7,
        first_dose_hour=20,
    )
    weight = compute_weight_metrics(patient)
    renal = compute_renal_metrics(patient, weight)
    assert renal.gfr_band == 3

    result = compute_doses(patient, weight, renal, now=reference_now)
    assert result.first_dose_mg == 600
    assert result.second_dose_mg == 400
    assert result.third_dose_mg == 600
    assert result.instructions[0] == " Gis umiddelbart  -   24.08 20:00"
    assert result.instructions[1] == " Gis 25.08 12:00"
    assert result.instructions[2] == " Gis 26.08 12:00"


def test_high_gfr_second_dose_matches_excel_for_evening_dose(reference_now: datetime):
    patient = PatientInput(
        sex="male",
        age_years=25,
        weight_kg=75,
        height_cm=180,
        creatinine_umol_l=60,
        mg_per_kg=6,
        first_dose_hour=20,
    )
    weight = compute_weight_metrics(patient)
    renal = compute_renal_metrics(patient, weight)
    result = compute_doses(patient, weight, renal, now=reference_now)
    assert result.second_dose_mg == 280


def test_high_gfr_second_dose_after_night_shift(reference_now: datetime):
    patient = PatientInput(
        sex="female",
        age_years=20,
        weight_kg=75,
        height_cm=180,
        creatinine_umol_l=110,
        mg_per_kg=4,
        first_dose_hour=8,
    )
    weight = compute_weight_metrics(patient)
    renal = compute_renal_metrics(patient, weight)
    result = compute_doses(patient, weight, renal, now=reference_now)
    assert result.second_dose_mg == result.first_dose_mg
    assert result.third_dose_mg == result.first_dose_mg


def test_high_gfr_second_dose_keeps_cap(reference_now: datetime):
    patient = PatientInput(
        sex="female",
        age_years=20,
        weight_kg=200,
        height_cm=170,
        creatinine_umol_l=110,
        mg_per_kg=6,
        first_dose_hour=8,
    )
    weight = compute_weight_metrics(patient)
    renal = compute_renal_metrics(patient, weight)
    result = compute_doses(patient, weight, renal, now=reference_now)
    assert result.first_dose_mg == 600
    assert result.second_dose_mg == 600
    assert result.third_dose_mg == 600


def test_high_gfr_second_dose_reduced_from_capped(reference_now: datetime):
    patient = PatientInput(
        sex="female",
        age_years=20,
        weight_kg=160,
        height_cm=190,
        creatinine_umol_l=150,
        mg_per_kg=6,
        first_dose_hour=1,
    )
    weight = compute_weight_metrics(patient)
    renal = compute_renal_metrics(patient, weight)
    result = compute_doses(patient, weight, renal, now=reference_now)
    assert result.first_dose_mg == 600
    assert result.second_dose_mg == 280
    assert result.third_dose_mg == 600


def test_high_gfr_evening_dose_has_reduction(reference_now: datetime):
    patient = PatientInput(
        sex="female",
        age_years=20,
        weight_kg=35,
        height_cm=140,
        creatinine_umol_l=30,
        mg_per_kg=4,
        first_dose_hour=20,
    )
    weight = compute_weight_metrics(patient)
    renal = compute_renal_metrics(patient, weight)
    result = compute_doses(patient, weight, renal, now=reference_now)
    assert result.first_dose_mg == 160
    assert result.second_dose_mg == 80
