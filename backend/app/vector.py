import os
from functools import lru_cache
from typing import List
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from .config import VECTOR_DIR, get_openai_key
from .schemas import Question, Answer


@lru_cache(maxsize=1)
def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(openai_api_key=get_openai_key())


@lru_cache(maxsize=1)
def get_vectorstore() -> FAISS:
    if not os.path.isdir(VECTOR_DIR):
        raise RuntimeError(
            f"Vector store not found in '{VECTOR_DIR}'. Run ingest.py first."
        )
    return FAISS.load_local(VECTOR_DIR, get_embeddings())


def ask_question(payload: Question) -> Answer:
    if not payload.question:
        raise ValueError("Question cannot be empty")
    store = get_vectorstore()
    docs = store.similarity_search(payload.question, k=4)
    llm = ChatOpenAI(openai_api_key=get_openai_key())
    chain = load_qa_chain(llm, chain_type="stuff")
    answer_text = chain.run(input_documents=docs, question=payload.question)
    sources = [doc.metadata.get("source", "") for doc in docs]
    return Answer(answer=answer_text, sources=sources)


def list_documents() -> List[str]:
    store = get_vectorstore()
    return [meta.get("source", "") for meta in store.docstore._dict.values()]
