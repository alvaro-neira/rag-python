"""
Middleware to collect Prometheus metrics for HTTP requests
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.metrics import metrics_recorder
from app.core.logging_config import get_logger


def _get_endpoint_name(path: str) -> str:
    """Normalize endpoint path for metrics (remove dynamic parts)"""
    # Replace common dynamic parts to avoid high cardinality
    if path.startswith("/query"):
        return "/query"
    elif path.startswith("/ingest"):
        return "/ingest"
    elif path.startswith("/health"):
        return "/health"
    elif path.startswith("/metrics"):
        return "/metrics"
    else:
        return path


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP request metrics"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger("metrics_middleware")

    async def dispatch(self, request: Request, call_next):
        # Extract request info
        method = request.method
        path = request.url.path
        endpoint = _get_endpoint_name(path)
        
        # Start tracking request
        tracking_key = metrics_recorder.record_http_request_start(method, endpoint)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record successful response
            metrics_recorder.record_http_request_end(
                tracking_key, method, endpoint, response.status_code
            )
            
            return response
            
        except Exception as e:
            # Record error response (assume 500 for exceptions)
            metrics_recorder.record_http_request_end(
                tracking_key, method, endpoint, 500
            )
            
            # Record error metrics
            metrics_recorder.record_error(
                error_type=type(e).__name__,
                operation="http_request"
            )
            
            # Re-raise the exception
            raise