#!/bin/bash

cd "$(dirname "$0")"

export PYTHONPATH=$(pwd)

if [ ! -d ".venv" ]; then
  echo "🛠️  .venv not found, creating .venv..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Launching server..."
uvicorn backend.app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info \
  --timeout-keep-alive 60
