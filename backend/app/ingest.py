"""Document ingestion script."""

import os
from pathlib import Path
from typing import List

from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredMarkdownLoader,
)

from .config import VECTOR_DIR, BASE_DIR, get_openai_key

DOCS_DIR = BASE_DIR / "docs"


def load_documents(source_dir: str) -> List[str]:
    """Recursively load documents from ``source_dir``."""
    docs = []
    for path in Path(source_dir).rglob("*"):
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            loader = PyPDFLoader(str(path))
        elif suffix == ".md":
            loader = UnstructuredMarkdownLoader(str(path))
        elif suffix in {".txt", ".text"}:
            loader = TextLoader(str(path))
        else:
            continue
        docs.extend(loader.load())
    return docs


def main():
    """Build or update the FAISS vector store from documents."""
    if not DOCS_DIR.is_dir():
        raise RuntimeError(f"Docs directory '{DOCS_DIR}' not found")

    embeddings = OpenAIEmbeddings(openai_api_key=get_openai_key())
    documents = load_documents(str(DOCS_DIR))
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = splitter.split_documents(documents)

    if os.path.isdir(VECTOR_DIR):
        store = FAISS.load_local(VECTOR_DIR, embeddings)
        store.add_documents(split_docs)
    else:
        store = FAISS.from_documents(split_docs, embeddings)
    store.save_local(VECTOR_DIR)
    print(f"Saved vector store to {VECTOR_DIR}")


if __name__ == "__main__":
    main()
