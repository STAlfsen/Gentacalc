import json
from pathlib import Path


def test_alert_texts_fixture_contains_expected_keys():
    payload = json.loads(
        Path("gentacalc/data/alert_texts.json").read_text(encoding="utf-8")
    )
    for key in [
        "under_80_guidance",
        "over_80_guidance",
        "bmi_over_35",
        "dose_over_600",
        "creatinine_floor",
    ]:
        assert key in payload
        assert payload[key], key


def test_default_snapshot_fixture_matches_expected_shape():
    snapshot = json.loads(Path("tests/fixtures/default_snapshot.json").read_text())
    assert "Gentacalc" in snapshot
    assert "Ark2" in snapshot
    assert snapshot["Gentacalc"]["C21"] == 45
    assert snapshot["Ark2"]["G43"] == 280
