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

from .config import VECTOR_DIR, DOCS_DIR, get_openai_key


def load_file(path: Path):
    """Load a single document based on file extension."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        loader = PyPDFLoader(str(path))
    elif suffix == ".md":
        loader = UnstructuredMarkdownLoader(str(path))
    elif suffix in {".txt", ".text"}:
        loader = TextLoader(str(path))
    else:
        return []
    return loader.load()


def load_documents(source_dir: str) -> List[str]:
    """Recursively load all supported documents from ``source_dir``."""
    docs = []
    for path in Path(source_dir).rglob("*"):
        docs.extend(load_file(path))
    return docs


def ingest_paths(paths: List[str]) -> None:
    """Add the given file paths to the FAISS store."""
    embeddings = OpenAIEmbeddings(openai_api_key=get_openai_key())
    documents = []
    for p in paths:
        documents.extend(load_file(Path(p)))
    if not documents:
        return
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = splitter.split_documents(documents)

    if os.path.isdir(VECTOR_DIR):
        add_documents(split_docs)
    else:
        store = FAISS.from_documents(split_docs, embeddings)
        store.save_local(VECTOR_DIR)


def main():
    """Build or update the FAISS vector store from documents."""
    if not DOCS_DIR.is_dir():
        raise RuntimeError(f"Docs directory '{DOCS_DIR}' not found")

    ingest_paths([str(p) for p in Path(DOCS_DIR).rglob("*")])
    print(f"Saved vector store to {VECTOR_DIR}")


if __name__ == "__main__":
    main()
