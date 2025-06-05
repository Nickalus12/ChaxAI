from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import Question, Answer
from .vector import ask_question, list_documents

app = FastAPI(title="ChaxAI Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/documents", response_model=list[str])
def documents() -> list[str]:
    return list_documents()


@app.post("/ask", response_model=Answer)
def ask(payload: Question) -> Answer:
    try:
        return ask_question(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
