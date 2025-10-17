from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import math

from .models import PatientInput
from .anthropometrics import WeightMetrics
from .renal import RenalMetrics


@dataclass
class DoseResult:
    first_dose_mg: Optional[float]
    second_dose_mg: Optional[float]
    third_dose_mg: Optional[float]
    instructions: tuple[str, str, str]


CAUTION_TEXT = " Gentamicin anbefales ikke ved GFR <40.  "


def _round_to_multiple(value: float, multiple: int) -> int:
    quotient = value / multiple
    lower = math.floor(quotient)
    upper = math.ceil(quotient)
    if quotient - lower == upper - quotient:
        chosen = upper
    elif quotient - lower < upper - quotient:
        chosen = lower
    else:
        chosen = upper
    return int(chosen * multiple)


def _format_datetime(dt: datetime) -> str:
    return dt.strftime("%d.%m %H:%M")


def compute_doses(
    patient: PatientInput,
    weight: WeightMetrics,
    renal: RenalMetrics,
    *,
    now: Optional[datetime] = None,
) -> DoseResult:
    current_time = now or datetime.now()
    gfr_band = renal.gfr_band

    if not gfr_band or gfr_band == 1:
        return DoseResult(
            first_dose_mg=None,
            second_dose_mg=None,
            third_dose_mg=None,
            instructions=(CAUTION_TEXT, CAUTION_TEXT, CAUTION_TEXT),
        )

    first_raw = patient.mg_per_kg * weight.dosing_weight
    first_final = 600 if first_raw > 600 else _round_to_multiple(first_raw, 40)

    hours_offset = patient.first_dose_hour - 12
    if patient.first_dose_hour < 12:
        hours_offset += 24
    reduction_factor = 0 if hours_offset <= 3 else hours_offset * 0.04167
    reduction_factor = min(reduction_factor, 1)
    within_window = 0 if hours_offset > 19 else 1

    second_base = min(600, first_raw)

    if gfr_band == 2:
        second_raw = first_final
        third_raw: Optional[float] = None
    else:  # gfr_band == 3
        if within_window == 0:
            second_raw = first_final
        else:
            second_raw = second_base * (1 - reduction_factor)
        third_raw = first_raw

    second_final: Optional[int]
    if second_raw is None or (isinstance(second_raw, float) and second_raw == 0):
        second_final = None if second_raw is None else 0
    else:
        second_final = (
            600 if second_raw > 600 else _round_to_multiple(second_raw, 40)
        )

    if third_raw is None:
        third_final: Optional[int] = None
    else:
        third_final = (
            600 if first_raw > 600 else _round_to_multiple(third_raw, 40)
        )

    base_date = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    first_datetime = base_date + timedelta(hours=patient.first_dose_hour)

    if gfr_band == 3:
        first_instruction = (
            f" Gis umiddelbart  -   {_format_datetime(current_time.replace(hour=patient.first_dose_hour, minute=0))}"
        )
        if patient.first_dose_hour > 7:
            second_instruction = (
                f" Gis {_format_datetime((current_time + timedelta(days=1)).replace(hour=12, minute=0))}"
            )
            third_instruction = (
                f" Gis {_format_datetime((current_time + timedelta(days=2)).replace(hour=12, minute=0))}"
            )
        else:
            second_instruction = (
                f" Gis {_format_datetime(current_time.replace(hour=12, minute=0))}"
            )
            third_instruction = (
                f" Gis {_format_datetime((current_time + timedelta(days=1)).replace(hour=12, minute=0))}"
            )
    else:
        first_instruction = (
            f" Gis umiddelbart  -  {_format_datetime(current_time.replace(hour=patient.first_dose_hour, minute=0))}"
        )
        second_time = first_datetime + timedelta(hours=36)
        second_instruction = (
            " Gis 36 timer etter dose 1  -  "
            f"{_format_datetime(second_time)}"
        )
        third_instruction = " Tredje dose Gentamicin skal ikke gis"

    return DoseResult(
        first_dose_mg=int(first_final),
        second_dose_mg=None if second_final is None else int(second_final),
        third_dose_mg=None if third_final is None else int(third_final),
        instructions=(first_instruction, second_instruction, third_instruction),
    )
