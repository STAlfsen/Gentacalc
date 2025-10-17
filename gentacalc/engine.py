from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from .alerts import collect_alerts
from .anthropometrics import compute_weight_metrics
from .dosing import compute_doses
from .models import CalculationContext, DosingPlan, PatientInput
from .renal import compute_renal_metrics


def _format_dt(dt: datetime) -> str:
    return dt.strftime("%d.%m %H:%M")


def _monitoring_recommendation(
    reference: datetime, gfr_band: Optional[int], first_hour: int
) -> Optional[str]:
    if gfr_band is None:
        return None

    if gfr_band >= 3:
        days = 2 if 1 <= first_hour <= 7 else 3
    elif gfr_band == 2:
        days = 3 if 12 <= first_hour <= 24 else 2
    else:
        return None

    target = (reference + timedelta(days=days)).replace(hour=8, minute=0, second=0, microsecond=0)
    return f"Vurder videre bruk: {_format_dt(target)}"


def calculate_plan(patient: PatientInput, *, now: Optional[datetime] = None) -> DosingPlan:
    if patient.age_years < 16:
        raise ValueError("Kalkulatoren støtter ikke pasienter under 16 år.")
    weight = compute_weight_metrics(patient)
    renal = compute_renal_metrics(patient, weight)
    reference_time = now or datetime.now()
    doses = compute_doses(patient, weight, renal, now=reference_time)
    alerts = collect_alerts(patient, weight, renal)
    monitoring = _monitoring_recommendation(reference_time, renal.gfr_band, patient.first_dose_hour)

    context = CalculationContext(
        bmi=weight.bmi,
        ideal_body_weight=weight.ideal_body_weight,
        adjusted_body_weight=weight.adjusted_body_weight,
        dosing_weight=weight.dosing_weight,
        cockcroft_gault=renal.cockcroft_gault_male,
        cockcroft_gault_female=renal.cockcroft_gault_female,
        cockcroft_gault_bmi_29_9=renal.cockcroft_gault_bmi_29_9,
        chosen_gfr=renal.chosen_gfr,
        creatinine_used=renal.creatinine_used,
        gfr_band=renal.gfr_band,
    )

    return DosingPlan(
        first_dose_mg=doses.first_dose_mg,
        second_dose_mg=doses.second_dose_mg,
        third_dose_mg=doses.third_dose_mg,
        instructions=doses.instructions,
        alerts=alerts,
        context=context,
        monitoring=monitoring,
    )
