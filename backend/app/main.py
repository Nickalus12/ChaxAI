from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from pathlib import Path
from .utils import secure_filename
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File
from .middleware import RequestIDMiddleware, SecurityHeadersMiddleware

from .schemas import Question, Answer, DocumentInfo
from .vector import ask_question, list_documents
from .ingest import ingest_paths, rebuild_store
from .config import (
    ALLOWED_ORIGINS,
    DOCS_DIR,
    VECTOR_DIR,
    LLM_PROVIDER,
    configure_logging,
    MAX_UPLOAD_MB,
)
import logging
from .security import verify_token

configure_logging()
logger = logging.getLogger("chaxai.api")
logger.info("Using %s model provider", LLM_PROVIDER)
app = FastAPI(title="ChaxAI Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)


@app.get("/health")
def health() -> dict:
    logger.debug("Health check")
    return {"status": "ok"}


@app.get("/documents", response_model=list[DocumentInfo])
def documents(_: None = Depends(verify_token)) -> list[DocumentInfo]:
    docs = list_documents()
    logger.info("Listed %s documents", len(docs))
    return docs


@app.post("/ask", response_model=Answer)
def ask(payload: Question, _: None = Depends(verify_token)) -> Answer:
    try:
        ans = ask_question(payload)
        logger.info("Answered question: %s", payload.question)
        return ans
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/upload")
async def upload(
    background: BackgroundTasks,
    files: list[UploadFile] = File(...),
    _: None = Depends(verify_token),
) -> dict:
    paths = []
    for uploaded in files:
        ext = Path(uploaded.filename).suffix.lower()
        if ext not in {".pdf", ".md", ".txt", ".text"}:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {uploaded.filename}",
            )
        if uploaded.size is not None and uploaded.size > MAX_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {uploaded.filename}",
            )
        try:
            safe_name = secure_filename(uploaded.filename)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid filename")
        dest = DOCS_DIR / safe_name
        try:
            data = await uploaded.read()
        except Exception as exc:
            logger.error("Error reading upload %s: %s", uploaded.filename, exc)
            raise HTTPException(status_code=400, detail="Failed to read upload") from exc
        if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"File too large: {uploaded.filename}")
        try:
            with dest.open("wb") as f:
                f.write(data)
        except OSError as exc:
            logger.error("Error saving upload %s: %s", uploaded.filename, exc)
            raise HTTPException(status_code=500, detail="Failed to save file") from exc
        paths.append(str(dest))
    logger.info("Received %s files for upload", len(paths))
    background.add_task(ingest_paths, paths)
    return {"uploaded": [Path(p).name for p in paths]}


@app.delete("/documents/{name}")
def delete_document(name: str, _: None = Depends(verify_token)) -> dict:
    try:
        safe_name = secure_filename(name)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename")
    file_path = DOCS_DIR / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")
    file_path.unlink()
    try:
        rebuild_store()
    except RuntimeError:
        # Last document removed; clear vector store directory
        for f in Path(VECTOR_DIR).glob("*"):
            f.unlink()
        logger.info("Vector store cleared after deleting last document")
    logger.info("Deleted document %s", name)
    return {"deleted": name}
