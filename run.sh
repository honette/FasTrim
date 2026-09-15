#!/bin/sh
cd "$(dirname "$0")"
if [ -x .venv/bin/python ]; then
  exec .venv/bin/python -m fastrim "$@"
fi
exec python3 -m fastrim "$@"
