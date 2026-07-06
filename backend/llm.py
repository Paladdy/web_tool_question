import httpx

from config import settings
from prompts import SYSTEM_PROMPT, build_user_message


class LLMError(Exception):
    """Ошибка при обращении к LLM API."""


class LLMNotConfiguredError(LLMError):
    """API-ключ не задан."""


async def analyze_answer(answer: str) -> dict[str, str | bool]:
    if not settings.llm_configured:
        raise LLMNotConfiguredError(
            "Задайте LLM_API_KEY в .env. Бесплатный ключ: https://console.groq.com/keys"
        )

    reply = await _call_llm(answer)
    return {
        "reply": reply,
        "mode": "llm",
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "is_closing": _looks_like_closing(reply),
    }


async def _call_llm(answer: str) -> str:
    url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_message(answer)},
        ],
        "temperature": 0.4,
        "max_tokens": 300,
    }
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                if not content or not str(content).strip():
                    raise LLMError("LLM API вернул пустой ответ")
                return str(content).strip()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:400]
            if exc.response.status_code == 429:
                raise LLMError(
                    "Превышен лимит запросов Groq (429). Подождите минуту и попробуйте снова."
                ) from exc
            if exc.response.status_code in (401, 403):
                raise LLMError(
                    "Неверный или просроченный LLM_API_KEY. Проверьте ключ на console.groq.com/keys"
                ) from exc
            raise LLMError(
                f"LLM API вернул ошибку {exc.response.status_code}: {detail}"
            ) from exc
        except httpx.ConnectError as exc:
            last_error = exc
            if attempt == 0:
                continue
            raise LLMError(
                "Не удалось подключиться к Groq API. Проверьте интернет; "
                "если Groq недоступен в вашем регионе — включите VPN."
            ) from exc
        except httpx.TimeoutException as exc:
            last_error = exc
            if attempt == 0:
                continue
            raise LLMError(
                "Groq API не ответил вовремя. Попробуйте ещё раз через несколько секунд."
            ) from exc
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("LLM API вернул неожиданный формат ответа") from exc
        except httpx.HTTPError as exc:
            raise LLMError(f"Ошибка сети при обращении к LLM API: {exc}") from exc

    raise LLMError("Не удалось получить ответ от LLM API") from last_error


def _looks_like_closing(reply: str) -> bool:
    if "?" in reply:
        return False
    lowered = reply.lower()
    closing_markers = (
        "спасибо",
        "благодар",
        "заверш",
        "на этом интервью",
        "это всё",
    )
    return any(marker in lowered for marker in closing_markers)
