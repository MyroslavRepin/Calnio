#!/bin/zsh

export PYTHONPATH=$(pwd)

uvicorn backend.app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info \
  --timeout-keep-alive 60
