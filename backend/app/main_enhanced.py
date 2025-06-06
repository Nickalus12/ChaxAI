"""Enhanced FastAPI application with enterprise features."""

from fastapi import (
    FastAPI,
    HTTPException,
    BackgroundTasks,
    Depends,
    Request,
    UploadFile,
    WebSocket,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import logging
from typing import Optional
import json

from .config import (
    ALLOWED_ORIGINS, configure_logging, validate_config,
    ENABLE_MULTI_TENANT, ENABLE_ANALYTICS
)
from .middleware import (
    RequestIDMiddleware, SecurityHeadersMiddleware,
    RateLimitMiddleware, TenantMiddleware
)
from .schemas_enhanced import (
    Question, Answer, DocumentInfo, UploadResponse,
    ChatRequest, ChatResponse, SystemStatus
)
from .security_enhanced import get_current_user, User
from .vector_enhanced import vector_manager
from .ingest_enhanced import IngestManager
from .analytics import init_analytics, get_analytics_summary
from .websocket import websocket_endpoint

# Configure logging
configure_logging()
logger = logging.getLogger("chaxai.api")

# Validate configuration
validate_config()

# Initialize analytics if enabled
if ENABLE_ANALYTICS:
    init_analytics()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting ChaxAI Enterprise...")
    
    # Preload vector stores for better performance
    if not ENABLE_MULTI_TENANT:
        await vector_manager.get_store("default").load_store()
    
    yield
    
    # Shutdown
    logger.info("Shutting down ChaxAI Enterprise...")


# Create FastAPI app
app = FastAPI(
    title="ChaxAI Enterprise",
    description="Enterprise-grade AI-powered chat system with Grok integration",
    version="2.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

if ENABLE_MULTI_TENANT:
    app.add_middleware(TenantMiddleware)


# Routes

@app.get("/", response_model=SystemStatus)
async def root():
    """Get system status and information."""
    return SystemStatus(
        status="operational",
        version="2.0.0",
        features={
            "multi_tenant": ENABLE_MULTI_TENANT,
            "analytics": ENABLE_ANALYTICS,
            "streaming": True,
            "grok_model": "grok-beta"
        }
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "chaxai-enterprise"}


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """Chat endpoint with streaming support."""
    try:
        answer = await vector_manager.ask_question(
            Question(question=request.message),
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id
        )
        
        return ChatResponse(
            message=answer.answer,
            sources=answer.sources,
            confidence=answer.confidence,
            model_used=answer.model_used
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Chat processing failed")


@app.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """Streaming chat endpoint."""
    
    async def generate():
        try:
            # This is a simplified version - in production, you'd stream from Grok
            answer = await vector_manager.ask_question(
                Question(question=request.message),
                tenant_id=current_user.tenant_id,
                user_id=current_user.user_id
            )
            
            # Simulate streaming by sending chunks
            words = answer.answer.split()
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i:i+3]) + " "
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            
            # Send metadata
            yield f"data: {json.dumps({'done': True, 'sources': answer.sources})}\n\n"
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@app.get("/documents", response_model=list[DocumentInfo])
async def list_documents(
    current_user: User = Depends(get_current_user)
):
    """List documents for the current tenant."""
    store = vector_manager.get_store(current_user.tenant_id)
    docs = []
    
    for doc_id, metadata in store.metadata_store.items():
        if metadata["metadata"].get("tenant_id") == current_user.tenant_id:
            docs.append(DocumentInfo(
                id=doc_id,
                name=metadata["metadata"].get("source", "Unknown"),
                size=metadata["metadata"].get("char_count", 0),
                uploaded_at=metadata["metadata"].get("indexed_at"),
                metadata=metadata["metadata"]
            ))
    
    return docs


@app.post("/upload", response_model=UploadResponse)
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: list[UploadFile],
    current_user: User = Depends(get_current_user)
):
    """Upload and process documents."""
    ingest_manager = IngestManager(current_user.tenant_id)
    
    # Validate files
    validated_files = []
    for file in files:
        try:
            validated = await ingest_manager.validate_file(file)
            validated_files.append(validated)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Process files in background
    task_id = await ingest_manager.queue_ingestion(
        validated_files,
        user_id=current_user.user_id
    )
    
    background_tasks.add_task(
        ingest_manager.process_queue
    )
    
    return UploadResponse(
        task_id=task_id,
        files_queued=len(validated_files),
        message="Files queued for processing"
    )


@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a document."""
    store = vector_manager.get_store(current_user.tenant_id)
    
    if document_id not in store.metadata_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check ownership
    doc_metadata = store.metadata_store[document_id]
    if doc_metadata["metadata"].get("tenant_id") != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Remove from metadata store
    del store.metadata_store[document_id]
    store._save_metadata()
    
    # Note: Full removal from FAISS requires rebuilding the index
    # In production, you might want to mark as deleted and rebuild periodically
    
    logger.info(f"Deleted document {document_id} for tenant {current_user.tenant_id}")
    
    return {"status": "deleted", "document_id": document_id}


@app.get("/analytics/summary")
async def get_analytics(
    current_user: User = Depends(get_current_user)
):
    """Get analytics summary for the tenant."""
    if not ENABLE_ANALYTICS:
        raise HTTPException(status_code=404, detail="Analytics not enabled")
    
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    summary = await get_analytics_summary(current_user.tenant_id)
    return summary


@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    """WebSocket endpoint for real-time chat."""
    await websocket_endpoint(websocket)


# Widget-specific endpoints

@app.get("/widget/config")
async def widget_config(origin: Optional[str] = None):
    """Get widget configuration for the requesting origin."""
    # In production, validate the origin against allowed domains
    return {
        "features": {
            "streaming": True,
            "file_upload": True,
            "voice_input": False,
            "markdown_support": True
        },
        "branding": {
            "name": "ChaxAI Assistant",
            "theme": "light",
            "primary_color": "#1976d2"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main_enhanced:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
