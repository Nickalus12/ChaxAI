from fastapi import FastAPI, HTTPException
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File

from .schemas import Question, Answer
from .vector import ask_question, list_documents
from .ingest import ingest_paths
from .config import ALLOWED_ORIGINS, DOCS_DIR

app = FastAPI(title="ChaxAI Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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


@app.post("/upload")
async def upload(files: list[UploadFile] = File(...)) -> dict:
    paths = []
    for uploaded in files:
        ext = Path(uploaded.filename).suffix.lower()
        if ext not in {".pdf", ".md", ".txt", ".text"}:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {uploaded.filename}",
            )
        dest = DOCS_DIR / uploaded.filename
        with dest.open("wb") as f:
            f.write(await uploaded.read())
        paths.append(str(dest))
    try:
        ingest_paths(paths)
    except Exception as exc:  # pragma: no cover - simple pass-through
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"uploaded": [Path(p).name for p in paths]}
