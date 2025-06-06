"""Enhanced Pydantic schemas for enterprise features."""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Question(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class Answer(BaseModel):
    answer: str
    sources: List[str]
    source_details: Optional[List[Dict[str, Any]]] = None
    confidence: float = Field(0.0, ge=0.0, le=100.0)
    model_used: Optional[str] = None
    request_id: Optional[str] = None
    processing_time: Optional[float] = None


class DocumentInfo(BaseModel):
    id: str
    name: str
    size: int
    uploaded_at: datetime
    metadata: Dict[str, Any]
    processing_status: Optional[str] = "completed"


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    stream: bool = False
    include_sources: bool = True
    max_tokens: Optional[int] = Field(None, ge=1, le=4000)
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0)


class ChatResponse(BaseModel):
    message: str
    sources: Optional[List[str]] = None
    confidence: Optional[float] = None
    model_used: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class UploadResponse(BaseModel):
    task_id: str
    files_queued: int
    message: str
    estimated_processing_time: Optional[int] = None


class SystemStatus(BaseModel):
    status: str
    version: str
    features: Dict[str, Any]
    uptime: Optional[int] = None
    health_checks: Optional[Dict[str, bool]] = None


class User(BaseModel):
    user_id: str
    tenant_id: str
    email: Optional[str] = None
    is_admin: bool = False
    permissions: List[str] = []
    metadata: Optional[Dict[str, Any]] = None


class AnalyticsSummary(BaseModel):
    tenant_id: str
    period: str
    total_queries: int
    total_tokens: int
    average_latency: float
    top_models: List[Dict[str, Any]]
    query_trends: List[Dict[str, Any]]
    error_rate: float