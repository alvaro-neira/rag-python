"""
Prometheus metrics configuration and collectors for the RAG microservice
"""
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from typing import Dict
import time


# Application info
app_info = Info('rag_microservice_info', 'RAG microservice information')
app_info.info({
    'version': '1.0.0',
    'service': 'rag-microservice',
})

# HTTP Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed',
    ['method', 'endpoint']
)

# RAG-specific business metrics
rag_queries_total = Counter(
    'rag_queries_total',
    'Total RAG queries processed',
    ['status']  # success, error
)

rag_query_duration_seconds = Histogram(
    'rag_query_duration_seconds',
    'RAG query processing time in seconds',
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 15.0, 30.0)
)

rag_sources_found = Histogram(
    'rag_sources_found',
    'Number of sources found per RAG query',
    buckets=(0, 1, 2, 3, 5, 10, 15, 20)
)

# Document ingestion metrics
document_ingestion_total = Counter(
    'document_ingestion_total',
    'Total document ingestion operations',
    ['status']  # success, error
)

document_ingestion_duration_seconds = Histogram(
    'document_ingestion_duration_seconds',
    'Document ingestion processing time in seconds',
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
)

documents_processed_total = Counter(
    'documents_processed_total',
    'Total number of documents processed'
)

# Vector store metrics
vector_store_operations_total = Counter(
    'vector_store_operations_total',
    'Total vector store operations',
    ['operation', 'status']  # operation: add, search; status: success, error
)

vector_store_collection_size = Gauge(
    'vector_store_collection_size',
    'Current number of documents in vector store collection'
)

# Embedding metrics
embeddings_generated_total = Counter(
    'embeddings_generated_total',
    'Total number of embeddings generated',
    ['type']  # document, query
)

embedding_generation_duration_seconds = Histogram(
    'embedding_generation_duration_seconds',
    'Time taken to generate embeddings in seconds',
    ['type'],  # document, query
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0)
)

# Error metrics
errors_total = Counter(
    'errors_total',
    'Total number of errors',
    ['error_type', 'operation']
)


class MetricsRecorder:
    """Helper class to record metrics with timing context"""
    
    def __init__(self):
        self._active_requests: Dict[str, float] = {}
    
    def record_http_request_start(self, method: str, endpoint: str) -> str:
        """Record start of HTTP request and return tracking key"""
        key = f"{method}:{endpoint}:{time.time()}"
        self._active_requests[key] = time.time()
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
        return key
    
    def record_http_request_end(self, key: str, method: str, endpoint: str, status_code: int):
        """Record end of HTTP request"""
        if key in self._active_requests:
            duration = time.time() - self._active_requests[key]
            del self._active_requests[key]
            
            # Record metrics
            http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
    
    def record_rag_query(self, duration_seconds: float, sources_count: int, success: bool = True):
        """Record RAG query metrics"""
        status = "success" if success else "error"
        rag_queries_total.labels(status=status).inc()
        
        if success:
            rag_query_duration_seconds.observe(duration_seconds)
            rag_sources_found.observe(sources_count)
    
    def record_document_ingestion(self, duration_seconds: float, documents_count: int, success: bool = True):
        """Record document ingestion metrics"""
        status = "success" if success else "error"
        document_ingestion_total.labels(status=status).inc()
        
        if success:
            document_ingestion_duration_seconds.observe(duration_seconds)
            documents_processed_total.inc(documents_count)
    
    def record_vector_store_operation(self, operation: str, success: bool = True):
        """Record vector store operation"""
        status = "success" if success else "error"
        vector_store_operations_total.labels(operation=operation, status=status).inc()
    
    def update_vector_store_size(self, size: int):
        """Update vector store collection size"""
        vector_store_collection_size.set(size)
    
    def record_embeddings_generated(self, count: int, embedding_type: str, duration_seconds: float):
        """Record embedding generation metrics"""
        embeddings_generated_total.labels(type=embedding_type).inc(count)
        embedding_generation_duration_seconds.labels(type=embedding_type).observe(duration_seconds)
    
    def record_error(self, error_type: str, operation: str):
        """Record error occurrence"""
        errors_total.labels(error_type=error_type, operation=operation).inc()


# Global metrics recorder instance
metrics_recorder = MetricsRecorder()


def get_metrics_content() -> tuple[str, str]:
    """Get Prometheus metrics content and content type"""
    return generate_latest(), CONTENT_TYPE_LATEST