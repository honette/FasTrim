@echo off
setlocal
cd /d "%~dp0"

set "PY=.venv_win\Scripts\python.exe"
if not exist "%PY%" set "PY=.venv\Scripts\python.exe"

if not exist "%PY%" (
    echo Python virtualenv not found.
    echo.
    echo Run once to set up:
    echo   python -m venv .venv_win
    echo   .venv_win/Scripts/activate
    echo   .venv_win/Scripts/pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

"%PY%" -m fastrim %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
    echo.
    echo FasTrim exited with error code %RC%.
    pause
)
endlocal
