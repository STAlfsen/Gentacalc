from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PatientInput:
    sex: str  # "male" or "female"
    age_years: float
    weight_kg: float
    height_cm: Optional[float]
    creatinine_umol_l: float
    mg_per_kg: float
    first_dose_hour: int


@dataclass(frozen=True)
class CalculationContext:
    """Intermediate metrics surfaced for testing and UI display."""

    bmi: Optional[float]
    ideal_body_weight: Optional[float]
    adjusted_body_weight: Optional[float]
    dosing_weight: float
    cockcroft_gault: Optional[float]
    cockcroft_gault_female: Optional[float]
    cockcroft_gault_bmi_29_9: Optional[float]
    chosen_gfr: Optional[float]
    creatinine_used: float
    gfr_band: Optional[int]


@dataclass(frozen=True)
class DosingPlan:
    first_dose_mg: Optional[float]
    second_dose_mg: Optional[float]
    third_dose_mg: Optional[float]
    instructions: tuple[str, str, str]
    alerts: tuple[str, ...]
    context: CalculationContext
    monitoring: Optional[str] = None
