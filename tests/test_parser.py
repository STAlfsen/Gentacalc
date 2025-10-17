import pytest

from gentacalc.parser import ValidationError, parse_patient


def test_parse_patient_success():
    payload = {
        "sex": "female",
        "age": "60",
        "weight": "70",
        "height": "165",
        "creatinine": "90",
        "mg_per_kg": "6",
        "first_dose_hour": "12",
    }
    patient = parse_patient(payload)
    assert patient.sex == "female"
    assert patient.age_years == 60
    assert patient.height_cm == 165
    assert patient.mg_per_kg == 6
    assert patient.first_dose_hour == 12


@pytest.mark.parametrize(
    "payload,error",
    [
        ({"sex": "unknown"}, "Kjønn må være 'kvinne' eller 'mann'"),
        (
            {
                "sex": "male",
                "age": "10",
                "weight": "70",
                "creatinine": "70",
                "mg_per_kg": "6",
                "first_dose_hour": "12",
            },
            "Alder må være minst 16",
        ),
        (
            {
                "sex": "female",
                "age": "60",
                "weight": "20",
                "creatinine": "70",
                "mg_per_kg": "6",
                "first_dose_hour": "12",
            },
            "Vekt må være minst 35",
        ),
        (
            {
                "sex": "female",
                "age": "60",
                "weight": "70",
                "creatinine": "25",
                "mg_per_kg": "6",
                "first_dose_hour": "12",
            },
            "Kreatinin må være minst 30",
        ),
        (
            {
                "sex": "female",
                "age": "60",
                "weight": "70",
                "creatinine": "70",
                "mg_per_kg": "9",
                "first_dose_hour": "12",
            },
            "Dose (mg/kg) må være høyst 7",
        ),
        (
            {
                "sex": "female",
                "age": "60",
                "weight": "70",
                "creatinine": "70",
                "mg_per_kg": "6",
                "first_dose_hour": "12.5",
            },
            "Klokkeslett for første dose må være en hel time",
        ),
    ],
)
def test_parse_patient_validation_errors(payload, error):
    with pytest.raises(ValidationError) as exc:
        parse_patient(payload)
    assert error in str(exc.value)
