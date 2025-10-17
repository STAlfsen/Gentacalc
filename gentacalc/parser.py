from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from .models import PatientInput


class ValidationError(ValueError):
    """Raised when incoming payload violates validation rules."""


def _require_number(
    payload: Mapping[str, Any],
    key: str,
    label: str,
    *,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
    required: bool = True,
    allow_empty: bool = False,
) -> Optional[float]:
    raw = payload.get(key)
    if raw in (None, ""):
        if required and not allow_empty:
            raise ValidationError(f"{label} må fylles ut")
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{label} må være et tall") from exc

    def format_bound(bound: float) -> str:
        return str(int(bound)) if float(bound).is_integer() else str(bound)

    if minimum is not None and value < minimum:
        raise ValidationError(f"{label} må være minst {format_bound(minimum)}")
    if maximum is not None and value > maximum:
        raise ValidationError(f"{label} må være høyst {format_bound(maximum)}")
    return value


def parse_patient(payload: Mapping[str, Any]) -> PatientInput:
    sex = str(payload.get("sex", "")).strip().lower()
    if sex not in {"female", "male"}:
        raise ValidationError("Kjønn må være 'kvinne' eller 'mann'")

    age = _require_number(payload, "age", "Alder", minimum=16, maximum=110)
    weight = _require_number(payload, "weight", "Vekt", minimum=35, maximum=250)
    height = _require_number(
        payload,
        "height",
        "Høyde",
        minimum=130,
        maximum=210,
        required=False,
        allow_empty=True,
    )
    creatinine = _require_number(payload, "creatinine", "Kreatinin", minimum=30, maximum=1000)
    mg_per_kg = _require_number(payload, "mg_per_kg", "Dose (mg/kg)", minimum=3, maximum=7)
    first_hour_value = _require_number(
        payload,
        "first_dose_hour",
        "Klokkeslett for første dose",
        minimum=1,
        maximum=24,
    )

    if (
        age is None
        or weight is None
        or creatinine is None
        or mg_per_kg is None
        or first_hour_value is None
    ):
        raise ValidationError("Påkrevd verdi mangler")

    if not float(first_hour_value).is_integer():
        raise ValidationError("Klokkeslett for første dose må være en hel time")

    return PatientInput(
        sex=sex,
        age_years=age,
        weight_kg=weight,
        height_cm=height,
        creatinine_umol_l=creatinine,
        mg_per_kg=mg_per_kg,
        first_dose_hour=int(first_hour_value),
    )
