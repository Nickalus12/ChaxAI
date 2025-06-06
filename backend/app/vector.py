import os
from functools import lru_cache
from typing import List
import logging
from langchain.docstore.document import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from .config import (
    VECTOR_DIR,
    LLM_PROVIDER,
    get_api_key,
    get_openai_key,
    get_api_base,
)
from .schemas import Question, Answer, DocumentInfo


@lru_cache(maxsize=1)
def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(openai_api_key=get_openai_key())


@lru_cache(maxsize=1)
def get_vectorstore() -> FAISS:
    if not os.path.isdir(VECTOR_DIR):
        raise RuntimeError(
            f"Vector store not found in '{VECTOR_DIR}'. Run ingest.py first."
        )
    logging.getLogger(__name__).info("Loading vector store from %s", VECTOR_DIR)
    return FAISS.load_local(VECTOR_DIR, get_embeddings())


def get_llm():
    """Instantiate the chat model based on ``LLM_PROVIDER``."""
    if LLM_PROVIDER == "openai":
        return ChatOpenAI(
            openai_api_key=get_api_key("openai"),
            openai_api_base=get_api_base("openai"),
        )
    if LLM_PROVIDER == "claude":
        return ChatAnthropic(
            api_key=get_api_key("claude"),
            base_url=get_api_base("claude"),
        )
    if LLM_PROVIDER == "grok":
        return ChatOpenAI(
            openai_api_key=get_api_key("grok"),
            openai_api_base=get_api_base("grok"),
        )
    raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")


def ask_question(payload: Question) -> Answer:
    if not payload.question:
        raise ValueError("Question cannot be empty")
    store = get_vectorstore()
    docs = store.similarity_search(payload.question, k=4)
    llm = get_llm()
    chain = load_qa_chain(llm, chain_type="stuff")
    answer_text = chain.run(input_documents=docs, question=payload.question)
    logging.getLogger(__name__).info("Answered question with %s sources", len(docs))
    sources = [doc.metadata.get("source", "") for doc in docs]
    return Answer(answer=answer_text, sources=sources)


def list_documents() -> List[DocumentInfo]:
    store = get_vectorstore()
    infos = []
    for meta in store.docstore._dict.values():
        src = meta.get("source", "")
        try:
            size = os.path.getsize(src)
        except OSError:
            size = 0
        infos.append(DocumentInfo(name=os.path.basename(src), size=size))
    return infos


def add_documents(docs: List[Document]) -> None:
    """Add documents to the cached vector store and persist."""
    store = get_vectorstore()
    store.add_documents(docs)
    store.save_local(VECTOR_DIR)
