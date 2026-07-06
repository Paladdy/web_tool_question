#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r backend/requirements.txt

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo ""
  echo "→ Создан .env. Получите бесплатный ключ: https://console.groq.com/keys"
  echo "→ Вставьте его в LLM_API_KEY и перезапустите ./run.sh"
  echo ""
fi

cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
