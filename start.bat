@echo off
cd /d "%~dp0backend"

if not exist "venv\Scripts\python.exe" (
    echo.
    echo Creating Python virtual environment...
    python -m venv venv

    echo.
    echo Installing project requirements...
    venv\Scripts\python.exe -m pip install -r requirements.txt
)

echo.
echo Starting Smart Waste Management System...
start "" venv\Scripts\python.exe app.py

timeout /t 3 /nobreak >nul

start "" http://127.0.0.1:5000/