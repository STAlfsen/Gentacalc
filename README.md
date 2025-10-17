# Gentacalc

Gentacalc is a Flask-based calculator for gentamicin dosing. The project exposes a small web UI and a JSON API backed by deterministic domain logic (`gentacalc/`).

## Project Layout

- `app.py` / `wsgi.py` – Flask entrypoints for local dev and production (Elastic Beanstalk uses `wsgi:application`).
- `gentacalc/` – Core dosing engine and supporting modules.
- `templates/index.html` – Single-page UI that talks to `/api/dose`.
- `tests/` – Pytest suite covering anthropometrics, renal metrics, dosing engine, and parser.
- `.aws/README.md` – Documentation of the AWS setup (Elastic Beanstalk app/env, IAM profiles, ACM certificate, deployment commands). Credentials are *not* tracked.

## Local Development
1. Ensure Python ≥ 3.11.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-excel-compare.txt  # optional dev tools
   ```
3. Run the app locally:
   ```bash
   flask --app app run --reload
   # or python app.py
   ```
4. Execute the test suite:
   ```bash
   pytest
   ```

## Scripts
The scripts folder contains python scripts to compare the output of the original gentacalc sheet with the webapp for validation purposes. Must be run in a windows environment with excel installed and Original_gentaCalc.xlsm present. Install libaries in 'requirements-excel-compare.txt'.

The instructions comparison in the compare compare_excel_with_python is not properly normalised, run analyse_instruction_mismatches on the resulting dataset to normalise and compare instructions. The resulting dose_mismatches.json and instruction_mismatches.json should return empty strings if no mismatches.