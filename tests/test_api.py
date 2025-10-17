import pytest

from app import app


@pytest.fixture
def client():
    app.config.update({"TESTING": True})
    with app.test_client() as client:
        yield client


def test_api_dose_happy_path(client):
    payload = {
        "sex": "female",
        "age": "72",
        "weight": "49",
        "height": "169",
        "mg_per_kg": "6",
        "creatinine": "77",
        "first_dose_hour": "23",
    }
    response = client.post("/api/dose", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["plan"]["first_dose_mg"] == 280
    assert data["plan"]["instructions"][2] == " Tredje dose Gentamicin skal ikke gis"
    assert data["plan"]["monitoring"].startswith("Vurder videre bruk")
    assert data["plan"]["alerts"] == []
    assert data["context"]["gfr_band"] == 2
    assert data["context"]["chosen_gfr"] == 45


def test_api_returns_validation_error(client):
    payload = {"sex": "unknown"}
    response = client.post("/api/dose", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert "Kjønn må være 'kvinne' eller 'mann'" in data["error"]
