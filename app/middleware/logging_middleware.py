import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging_config import get_logger, log_request, log_response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all incoming requests and responses"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger("middleware")
    
    async def dispatch(self, request: Request, call_next):
        # Record start time
        start_time = time.time()
        
        # Extract request details
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else None
        
        # Log request
        if query_params:
            log_request(self.logger, method, path, query_params=query_params)
        else:
            log_request(self.logger, method, path)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful response
            log_response(
                self.logger, 
                method, 
                path, 
                response.status_code, 
                duration_ms
            )
            
            return response
            
        except Exception as e:
            # Calculate duration for failed requests
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error response
            self.logger.error(
                f"{method} {path} - Error ({duration_ms:.2f}ms)",
                extra={
                    "event_type": "request_error",
                    "http_method": method,
                    "path": path,
                    "duration_ms": duration_ms,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )
            
            # Re-raise the exception
            raise