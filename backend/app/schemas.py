from pydantic import BaseModel
from typing import List


class Question(BaseModel):
    question: str


class Answer(BaseModel):
    answer: str
    sources: List[str]


class DocumentInfo(BaseModel):
    name: str
    size: int
