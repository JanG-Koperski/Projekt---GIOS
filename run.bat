@echo off
REM Uruchamia aplikację w środowisku virtualenv jeśli istnieje
IF EXIST .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)
python app.py
