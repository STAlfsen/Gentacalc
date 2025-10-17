from gentacalc.alerts import collect_alerts
from gentacalc.anthropometrics import compute_weight_metrics
from gentacalc.models import PatientInput
from gentacalc.renal import compute_renal_metrics


def build_context(patient: PatientInput):
    weight = compute_weight_metrics(patient)
    renal = compute_renal_metrics(patient, weight)
    return weight, renal


def test_creatinine_floor_alert_is_present():
    patient = PatientInput(
        sex="female",
        age_years=40,
        weight_kg=65,
        height_cm=170,
        creatinine_umol_l=50,
        mg_per_kg=5,
        first_dose_hour=12,
    )
    weight, renal = build_context(patient)
    alerts = collect_alerts(patient, weight, renal)
    assert any("Kreatinin" in alert for alert in alerts)


def test_bmi_alerts_triggered():
    patient = PatientInput(
        sex="female",
        age_years=50,
        weight_kg=120,
        height_cm=160,
        creatinine_umol_l=70,
        mg_per_kg=5,
        first_dose_hour=12,
    )
    weight, renal = build_context(patient)
    alerts = collect_alerts(patient, weight, renal)
    assert any("BMI" in alert for alert in alerts)


def test_dose_cap_alert_when_raw_exceeds_600():
    patient = PatientInput(
        sex="male",
        age_years=45,
        weight_kg=120,
        height_cm=185,
        creatinine_umol_l=65,
        mg_per_kg=8,
        first_dose_hour=20,
    )
    weight, renal = build_context(patient)
    alerts = collect_alerts(patient, weight, renal)
    assert any("600 mg" in alert for alert in alerts)
