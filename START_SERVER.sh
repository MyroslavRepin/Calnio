#!/bin/bash

cd "$(dirname "$0")"
export PYTHONPATH=$(pwd)

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [[ "$1" == "--reset" ]]; then
  echo -e "${YELLOW}🧹 Removing existing .venv...${NC}"
  rm -rf .venv
fi

if [[ "$1" == "--create_tables" ]]; then
  source .venv/bin/activate
  python3 manage.py create
fi

if [ ! -d ".venv" ]; then
  echo -e "${YELLOW}🛠️  .venv not found, creating...${NC}"
  python3 -m venv .venv
fi

if [ ! -f ".venv/bin/activate" ]; then
  echo -e "${RED}❌ Could not find .venv activation script.${NC}"
  exit 1
fi

source .venv/bin/activate

if [ ! -f "requirements.txt" ]; then
  echo -e "${RED}❌ requirements.txt not found!${NC}"
  exit 1
fi

echo -e "${GREEN}📦 Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}🚀 Launching server...${NC}"
if [[ "$1" == "--https" ]]; then
  echo "Running on HTTPS" && 
  uvicorn backend.app.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --log-level debug \
    --reload \
    --timeout-keep-alive 60 \
    --ssl-certfile localhost+2.pem \
    --ssl-keyfile localhost+2-key.pem
else
  uvicorn backend.app.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --log-level info \
    --reload \
    --timeout-keep-alive 60
fi
