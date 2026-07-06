import pytest
from httpx import ASGITransport, AsyncClient

from config import settings
from main import app


@pytest.fixture(autouse=True)
def llm_configured(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "gsk_test_key")


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["provider"] == "Groq"
    assert "llama" in data["model"]


@pytest.mark.asyncio
async def test_question():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/question")
    assert response.status_code == 200
    assert "курс" in response.json()["question"].lower()


@pytest.mark.asyncio
async def test_answer_superficial(monkeypatch):
    async def fake_llm(answer: str) -> str:
        return "Расскажите, пожалуйста, что именно повлияло на выбор — отзывы, цена или программа?"

    monkeypatch.setattr("llm._call_llm", fake_llm)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/answer", json={"answer": "Нашёл в интернете"})
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "llm"
    assert data["provider"] == "Groq"
    assert data["is_closing"] is False


@pytest.mark.asyncio
async def test_answer_detailed(monkeypatch):
    async def fake_llm(answer: str) -> str:
        return "Спасибо за развёрнутый ответ. На этом интервью можно завершить."

    monkeypatch.setattr("llm._call_llm", fake_llm)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/answer",
            json={"answer": "Сравнивал три платформы по отзывам и цене."},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["is_closing"] is True


@pytest.mark.asyncio
async def test_missing_api_key(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", None)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/answer", json={"answer": "Тест"})
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_empty_answer_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/answer", json={"answer": "   "})
    assert response.status_code == 422 or response.status_code == 400
