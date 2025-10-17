from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from .anthropometrics import WeightMetrics
from .models import PatientInput


@dataclass
class RenalMetrics:
    creatinine_used: float
    cockcroft_gault_male: Optional[float]
    cockcroft_gault_female: Optional[float]
    cockcroft_gault_bmi_29_9: Optional[float]
    chosen_gfr: Optional[float]
    gfr_band: Optional[int]


def compute_renal_metrics(patient: PatientInput, weight: WeightMetrics) -> RenalMetrics:
    creatinine_input = patient.creatinine_umol_l
    creatinine_used = max(creatinine_input, 60)

    normalized_sex = (patient.sex or "").strip().lower()
    is_male = normalized_sex in {"male", "mann", "m"}
    sex_factor = 1.0 if is_male else 0.85

    bmi = weight.bmi
    cockcroft_weight = patient.weight_kg
    if bmi is not None and bmi > 30 and weight.adjusted_body_weight:
        cockcroft_weight = weight.adjusted_body_weight

    cockcroft_raw: Optional[float] = None
    if creatinine_used > 0 and cockcroft_weight is not None:
        cockcroft_raw = ((140 - patient.age_years) * cockcroft_weight) / (
            0.814 * creatinine_used
        )

    cockcroft_male = math.floor(cockcroft_raw) if cockcroft_raw is not None else None
    cockcroft_female = (
        math.floor(cockcroft_raw * 0.85) if cockcroft_raw is not None else None
    )

    patient_cg = cockcroft_male if is_male else cockcroft_female

    bmi_surrogate: Optional[float] = None
    if patient.height_cm and creatinine_used > 0:
        height_m = patient.height_cm / 100
        numerator = (140 - patient.age_years) * 29.9 * (height_m**2)
        bmi_surrogate_raw = numerator / (0.814 * creatinine_used) * sex_factor
        bmi_surrogate = bmi_surrogate_raw

    chosen_gfr: Optional[float] = None
    if patient_cg is not None:
        if bmi is None or bmi <= 30:
            chosen_gfr = patient_cg
        else:
            if bmi_surrogate is not None:
                chosen_gfr = max(patient_cg, bmi_surrogate)
            else:
                chosen_gfr = patient_cg

    gfr_band: Optional[int] = None
    if chosen_gfr is not None:
        if chosen_gfr > 59:
            gfr_band = 3
        elif chosen_gfr >= 40:
            gfr_band = 2
        else:
            gfr_band = 1

    return RenalMetrics(
        creatinine_used=creatinine_used,
        cockcroft_gault_male=cockcroft_male,
        cockcroft_gault_female=cockcroft_female,
        cockcroft_gault_bmi_29_9=bmi_surrogate,
        chosen_gfr=chosen_gfr,
        gfr_band=gfr_band,
    )
