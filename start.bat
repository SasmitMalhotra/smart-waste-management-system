@echo off
cd /d "%~dp0backend"

call venv\Scripts\activate.bat

start "" python app.py

timeout /t 3 /nobreak >nul

start "" http://127.0.0.1:5000/