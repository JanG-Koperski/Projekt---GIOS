@echo off
SETLOCAL

REM --- Ścieżki ---
SET VENV_DIR=.venv
SET APP_PATH=app.py
SET REQ_FILE=requirements.txt

REM --- Tworzenie środowiska wirtualnego ---
IF NOT EXIST "%VENV_DIR%\Scripts\activate.bat" (
    echo Tworzenie nowego środowiska wirtualnego...
    python -m venv "%VENV_DIR%"
    IF ERRORLEVEL 1 (
        echo Blad: Nie udalo sie utworzyc srodowiska wirtualnego.
        pause
        exit /b 1
    )
) ELSE (
    echo Srodowisko wirtualne juz istnieje.
)

REM --- Aktywacja środowiska ---
CALL "%VENV_DIR%\Scripts\activate.bat"
IF ERRORLEVEL 1 (
    echo Blad: Nie udalo sie aktywowac srodowiska wirtualnego.
    pause
    exit /b 1
)

REM --- Aktualizacja pip ---
echo Aktualizacja pip...
python -m pip install --upgrade pip
IF ERRORLEVEL 1 (
    echo Blad: Nie udalo sie zaktualizowac pip.
    pause
    exit /b 1
)

REM --- Instalacja wymaganych pakietow ---
IF EXIST "%REQ_FILE%" (
    echo Instalacja pakietow z %REQ_FILE%...
    pip install -r "%REQ_FILE%"
    IF ERRORLEVEL 1 (
        echo Blad: Instalacja pakietow nie powiodla sie.
        pause
        exit /b 1
    )
) ELSE (
    echo Plik %REQ_FILE% nie istnieje!
    pause
    exit /b 1
)

REM --- Uruchomienie aplikacji ---
IF EXIST "%APP_PATH%" (
    echo Uruchamianie aplikacji...
    python "%APP_PATH%"
) ELSE (
    echo Plik aplikacji %APP_PATH% nie istnieje!
    pause
    exit /b 1
)

ENDLOCAL
