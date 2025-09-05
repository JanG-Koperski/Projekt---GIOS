@echo off
REM Ustaw bieżący katalog na ten, w którym znajduje się ten plik CMD
cd /d "%~dp0"

REM Aktywuj wirtualne środowisko
call .venv\Scripts\activate.bat

REM Uruchom pytest
pytest

REM Pauza, żeby widzieć wynik
pause