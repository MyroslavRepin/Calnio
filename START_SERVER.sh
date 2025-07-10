#!/bin/bash

cd "$(dirname "$0")"

export PYTHONPATH=$(pwd)

if [ ! -d ".venv" ]; then
  echo "🛠️  .venv не найден, создаю..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "📦 Устанавливаю зависимости из requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🚀 Запуск сервера..."
uvicorn backend.app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info \
  --timeout-keep-alive 60
