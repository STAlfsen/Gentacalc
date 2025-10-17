from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

from .models import PatientInput
from .anthropometrics import WeightMetrics
from .renal import RenalMetrics


DATA_PATH = Path(__file__).resolve().parent / "data" / "alert_texts.json"
ALERT_TEXTS = json.loads(DATA_PATH.read_text(encoding="utf-8"))


def _compose(key: str) -> Tuple[str, ...]:
    lines = ALERT_TEXTS.get(key, [])
    if not lines:
        return ()
    text = "\n".join(lines)
    return (text,)


def collect_alerts(
    patient: PatientInput,
    weight: WeightMetrics,
    renal: RenalMetrics,
) -> Tuple[str, ...]:
    alerts: list[str] = []
    bmi = weight.bmi

    if patient.creatinine_umol_l < 60:
        alerts.extend(_compose("creatinine_floor"))

    if bmi is not None:
        if bmi > 35 and (renal.chosen_gfr or 0) >= 40:
            alerts.extend(_compose("bmi_over_35"))
        elif 30 <= bmi < 35:
            alerts.extend(_compose("bmi_30_35"))

    raw_first_dose = patient.mg_per_kg * weight.dosing_weight
    if raw_first_dose > 600:
        alerts.extend(_compose("dose_over_600"))

    return tuple(alerts)
