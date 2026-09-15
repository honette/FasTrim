#!/bin/sh
cd "$(dirname "$0")"
if [ -x .venv/bin/python ]; then
  exec .venv/bin/python -m fastrim "$@"
fi
if [ -x .venv_win/Scripts/python.exe ]; then
  exec .venv_win/Scripts/python.exe -m fastrim "$@"
fi
if [ -x .venv_win/Scripts/python ]; then
  exec .venv_win/Scripts/python -m fastrim "$@"
fi
if command -v python3 >/dev/null 2>&1; then
  exec python3 -m fastrim "$@"
fi
exec python -m fastrim "$@"
