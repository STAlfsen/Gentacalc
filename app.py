from __future__ import annotations

from typing import Any, Mapping

from flask import Flask, jsonify, render_template, request

from gentacalc.engine import calculate_plan
from gentacalc.models import DosingPlan
from gentacalc.parser import ValidationError, parse_patient

app = Flask(__name__)


def _serialize_plan(plan: DosingPlan) -> dict[str, Any]:
    context = plan.context
    return {
        "plan": {
            "first_dose_mg": plan.first_dose_mg,
            "second_dose_mg": plan.second_dose_mg,
            "third_dose_mg": plan.third_dose_mg,
            "instructions": list(plan.instructions),
            "alerts": list(plan.alerts),
            "monitoring": plan.monitoring,
        },
        "context": {
            "bmi": context.bmi,
            "ideal_body_weight": context.ideal_body_weight,
            "adjusted_body_weight": context.adjusted_body_weight,
            "dosing_weight": context.dosing_weight,
            "cockcroft_gault_male": context.cockcroft_gault,
            "cockcroft_gault_female": context.cockcroft_gault_female,
            "cockcroft_gault_bmi_29_9": context.cockcroft_gault_bmi_29_9,
            "chosen_gfr": context.chosen_gfr,
            "creatinine_used": context.creatinine_used,
            "gfr_band": context.gfr_band,
        },
    }


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


def _extract_payload() -> Mapping[str, Any]:
    data = request.get_json(silent=True)
    if isinstance(data, dict):
        return data
    return request.form


@app.route("/api/dose", methods=["POST"])
def api_dose():
    payload = _extract_payload()
    try:
        patient = parse_patient(payload)
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400

    plan = calculate_plan(patient)
    return jsonify(_serialize_plan(plan))


if __name__ == "__main__":
    app.run(debug=True)
