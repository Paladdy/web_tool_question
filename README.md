# Интервью о выборе онлайн-курса

Микро-инструмент для качественного UX-интервью: пользователь отвечает на один вопрос, бэкенд на FastAPI отправляет ответ в **реальную LLM**, модель либо задаёт **один** уточняющий вопрос (если ответ поверхностный), либо благодарит и завершает беседу (если ответ подробный).

**Автор:** Даниил Рамкулов

## LLM: Groq (бесплатно)

Используется **[Groq](https://console.groq.com)** — бесплатный tier **без банковской карты**:

| Параметр | Значение |
|----------|----------|
| Модель | `llama-3.3-70b-versatile` (Meta Llama 3.3 70B) |
| Лимиты free tier | ~30 запросов/мин, ~1000 запросов/день |
| API | OpenAI-compatible |

### Получить ключ (2 минуты)

1. Зарегистрируйтесь на [console.groq.com](https://console.groq.com)
2. Создайте API Key: [console.groq.com/keys](https://console.groq.com/keys)
3. Скопируйте `.env.example` → `.env` и вставьте ключ:

```env
LLM_API_KEY=gsk_ваш_ключ
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
```

## Быстрый старт

```bash
cp .env.example .env   # вставьте ключ Groq
chmod +x run.sh
./run.sh
```

Откройте: [http://localhost:8000](http://localhost:8000)

## Ручной запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
cd backend && uvicorn main:app --reload --port 8000
```

## API

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/health` | Статус, провайдер, модель |
| GET | `/api/question` | Текст вопроса интервью |
| POST | `/api/answer` | `{ "answer": "..." }` → ответ исследователя |

## Тесты

Тесты мокают LLM — ключ для pytest не нужен.

```bash
source .venv/bin/activate
cd backend && pytest -q
```

## Структура

```
backend/
  main.py       — FastAPI, маршруты
  llm.py        — вызов Groq API
  prompts.py    — системный промпт и рубрика
  config.py     — настройки из .env
frontend/
  index.html    — одностраничный UI
COVER_LETTER.md — решения по промпту и архитектуре
```

## Видео

~1 мин: короткий ответ → уточняющий вопрос от Llama → подробный ответ → благодарность.
