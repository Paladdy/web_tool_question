from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config import settings
from llm import LLMError, LLMNotConfiguredError, analyze_answer
from prompts import RESEARCH_QUESTION

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"

app = FastAPI(
    title="Course Choice Interview",
    description="Микро-инструмент качественного UX-интервью с LLM",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnswerRequest(BaseModel):
    answer: str = Field(..., min_length=1, max_length=4000)


class AnswerResponse(BaseModel):
    question: str
    reply: str
    is_closing: bool
    mode: str
    provider: str | None = None
    model: str | None = None


@app.get("/api/health")
async def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "llm_configured": settings.llm_configured,
        "provider": settings.llm_provider,
        "model": settings.llm_model,
    }


@app.get("/api/question")
async def get_question() -> dict[str, str]:
    return {"question": RESEARCH_QUESTION}


@app.post("/api/answer", response_model=AnswerResponse)
async def submit_answer(payload: AnswerRequest) -> AnswerResponse:
    answer = payload.answer.strip()
    if not answer:
        raise HTTPException(status_code=400, detail="Ответ не может быть пустым")

    try:
        result = await analyze_answer(answer)
    except LLMNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return AnswerResponse(
        question=RESEARCH_QUESTION,
        reply=str(result["reply"]),
        is_closing=bool(result["is_closing"]),
        mode=str(result["mode"]),
        provider=str(result.get("provider") or settings.llm_provider),
        model=str(result.get("model") or settings.llm_model),
    )


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
