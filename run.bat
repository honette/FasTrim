@echo off
cd /d "%~dp0"
if exist ".venv_win\Scripts\python.exe" (
  ".venv_win\Scripts\python.exe" -m fastrim %*
) else if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m fastrim %*
) else (
  python -m fastrim %*
)
