"""Document ingestion script."""

import os
from pathlib import Path
from typing import List

from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from .vector import add_documents
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredMarkdownLoader,
)

from .config import VECTOR_DIR, DOCS_DIR, get_openai_key, get_api_base
import logging


def load_file(path: Path):
    """Load a single document based on file extension."""
    suffix = path.suffix.lower()
    try:
        if suffix == ".pdf":
            loader = PyPDFLoader(str(path))
        elif suffix == ".md":
            loader = UnstructuredMarkdownLoader(str(path))
        elif suffix in {".txt", ".text"}:
            loader = TextLoader(str(path))
        else:
            return []
        return loader.load()
    except Exception as exc:
        logger.warning("Failed to load %s: %s", path, exc)
        return []


def load_documents(source_dir: str) -> List[str]:
    """Recursively load all supported documents from ``source_dir``."""
    docs = []
    for path in Path(source_dir).rglob("*"):
        if path.is_file():
            docs.extend(load_file(path))
    return docs


logger = logging.getLogger(__name__)


def ingest_paths(paths: List[str]) -> None:
    """Add the given file paths to the FAISS store."""
    embeddings = OpenAIEmbeddings(
        openai_api_key=get_openai_key(),
        openai_api_base=get_api_base("openai"),
    )
    documents = []
    for p in paths:
        documents.extend(load_file(Path(p)))
    if not documents:
        logger.info("No valid documents found to ingest")
        return
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = splitter.split_documents(documents)

    try:
        if os.path.isdir(VECTOR_DIR):
            add_documents(split_docs)
            logger.info("Added %s documents to existing store", len(split_docs))
        else:
            store = FAISS.from_documents(split_docs, embeddings)
            store.save_local(VECTOR_DIR)
            logger.info("Created new vector store at %s", VECTOR_DIR)
    except Exception as exc:
        logger.error("Failed to update vector store: %s", exc)


def main():
    """Build or update the FAISS vector store from documents."""
    if not DOCS_DIR.is_dir():
        raise RuntimeError(f"Docs directory '{DOCS_DIR}' not found")

    ingest_paths([str(p) for p in Path(DOCS_DIR).rglob("*")])
    print(f"Saved vector store to {VECTOR_DIR}")


def rebuild_store() -> None:
    """Recreate the vector store from all documents."""
    docs = load_documents(str(DOCS_DIR))
    if not docs:
        if os.path.isdir(VECTOR_DIR):
            for f in Path(VECTOR_DIR).glob("*"):
                f.unlink()
            logger.info("Cleared empty vector store")
        raise RuntimeError("No documents available to rebuild vector store")
    embeddings = OpenAIEmbeddings(
        openai_api_key=get_openai_key(),
        openai_api_base=get_api_base("openai"),
    )
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = splitter.split_documents(docs)
    store = FAISS.from_documents(split_docs, embeddings)
    store.save_local(VECTOR_DIR)
    logger.info("Rebuilt vector store with %s documents", len(split_docs))


if __name__ == "__main__":
    main()
