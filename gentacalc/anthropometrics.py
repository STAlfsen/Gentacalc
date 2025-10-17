from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .models import PatientInput


@dataclass
class WeightMetrics:
    bmi: Optional[float]
    ideal_body_weight: Optional[float]
    adjusted_body_weight: Optional[float]
    dosing_weight: float


def compute_weight_metrics(patient: PatientInput) -> WeightMetrics:
    weight = patient.weight_kg
    height_cm = patient.height_cm
    bmi: Optional[float] = None
    if height_cm and height_cm > 0:
        bmi = weight / ((height_cm / 100) ** 2)

    normalized_sex = (patient.sex or "").strip().lower()
    ibw: Optional[float] = None
    if height_cm and height_cm > 0:
        if normalized_sex in {"male", "mann", "m"}:
            base = 50.0
        elif normalized_sex in {"female", "kvinne", "f"}:
            base = 45.5
        else:
            base = 45.5  # default to female formula if unspecified
        ibw = base + 0.9 * (height_cm - 152)

    adjusted_bw: Optional[float] = None
    if ibw is not None:
        adjusted_bw = ibw + 0.4 * (weight - ibw)

    dosing_weight = weight
    if ibw is not None and weight is not None:
        if ibw * 1.25 <= weight:
            ibw_times_factor = ibw * 1.249
            candidates = [c for c in (adjusted_bw, ibw_times_factor) if c is not None]
            dosing_weight = max(candidates) if candidates else weight

    return WeightMetrics(
        bmi=bmi,
        ideal_body_weight=ibw,
        adjusted_body_weight=adjusted_bw,
        dosing_weight=dosing_weight,
    )
