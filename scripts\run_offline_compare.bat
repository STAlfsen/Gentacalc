@echo off
setlocal enabledelayedexpansion

REM Run Excel/Python parity check using pre-downloaded wheels

set "ROOT_DIR=%~dp0.."
set "ROOT_DIR=%ROOT_DIR:\=/%"

set "VENV_DIR=%ROOT_DIR%/venv_compare"
set "WHEEL_DIR=%ROOT_DIR%/wheelhouse"
set "REQUIREMENTS_FILE=%ROOT_DIR%/requirements-excel-compare.txt"

if "%~1"=="" (
  set "WORKBOOK_PATH=%ROOT_DIR%/Original_gentaCalc.xlsm"
) else (
  set "WORKBOOK_PATH=%~1"
)

if "%~2"=="" (
  set "OUTPUT_PATH=%ROOT_DIR%/scripts/compare_results.json"
) else (
  set "OUTPUT_PATH=%~2"
)

if not "%MAX_SCENARIOS%"=="" (
  set "MAX_SCENARIOS=%MAX_SCENARIOS%"
) else (
  set "MAX_SCENARIOS=1500"
)

if not "%SEED%"=="" (
  set "SEED=%SEED%"
) else (
  set "SEED=2024"
)

if not exist "%WHEEL_DIR%" (
  echo Wheelhouse directory not found: %WHEEL_DIR%
  exit /b 1
)

if not exist "%REQUIREMENTS_FILE%" (
  echo Requirements file not found: %REQUIREMENTS_FILE%
  exit /b 1
)

if not exist "%WORKBOOK_PATH%" (
  echo Workbook not found: %WORKBOOK_PATH%
  exit /b 1
)

if not exist "%VENV_DIR%" (
  echo Creating virtual environment at %VENV_DIR%
  python -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo Failed to create virtual environment.
    exit /b 1
  )
)

call "%VENV_DIR%/Scripts/activate"

python -m pip install --upgrade pip >nul
python -m pip install --no-index --find-links "%WHEEL_DIR%" -r "%REQUIREMENTS_FILE%"
if errorlevel 1 (
  echo Failed to install dependencies.
  exit /b 1
)

python "%ROOT_DIR%/scripts/compare_excel_with_python.py" ^
  --workbook "%WORKBOOK_PATH%" ^
  --output "%OUTPUT_PATH%" ^
  --max-scenarios %MAX_SCENARIOS% ^
  --seed %SEED%

if errorlevel 1 (
  echo Comparison failed. Review output for details.
  exit /b 1
)

echo Comparison completed. Results saved to %OUTPUT_PATH%
endlocal
