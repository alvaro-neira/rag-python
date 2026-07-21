from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.rag_service import RAGService
from app.core.logging_config import get_logger, log_event, log_error
from app.core.metrics import get_metrics_content

# Initialize RAG service and logger
rag_service = RAGService()
logger = get_logger("api")

router = APIRouter()


# Request/Response Models
class QueryRequest(BaseModel):
    question: str


class SourceResponse(BaseModel):
    page: int
    text: str


class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]


class IngestResponse(BaseModel):
    status: str
    message: str
    total_documents: int
    sources: Dict[str, int]


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    content, content_type = get_metrics_content()
    return Response(content=content, media_type=content_type)


@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents():
    """Trigger document ingestion"""
    try:
        log_event(logger, "document_ingestion_started", "Starting document ingestion")
        
        result = rag_service.ingest_documents()
        
        log_event(
            logger, 
            "document_ingestion_completed", 
            "Document ingestion completed successfully",
            total_documents=result["total_documents"],
            sources=result["sources"]
        )
        
        return IngestResponse(
            status=result["status"],
            message=result["message"],
            total_documents=result["total_documents"],
            sources=result["sources"]
        )
    except Exception as e:
        log_error(logger, e, {"operation": "document_ingestion"})
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query documents using RAG"""
    try:
        log_event(
            logger, 
            "query_started", 
            "Processing RAG query",
            question=request.question,
            question_length=len(request.question)
        )
        
        result = rag_service.query(request.question)
        
        log_event(
            logger, 
            "query_completed", 
            "RAG query completed successfully",
            question=request.question,
            answer_length=len(result["answer"]),
            sources_found=len(result["sources"])
        )
        
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"]
        )
    except Exception as e:
        log_error(logger, e, {
            "operation": "rag_query",
            "question": request.question
        })
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
