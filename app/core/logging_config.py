import logging
import sys
import json
from typing import Dict, Any
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Base log structure
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": "rag-microservice",
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        extra_fields = {
            k: v for k, v in record.__dict__.items()
            if k not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'exc_info', 'exc_text',
                'stack_info'
            }
        }
        
        if extra_fields:
            log_data.update(extra_fields)
        
        return json.dumps(log_data, default=str)


def setup_logging() -> logging.Logger:
    """Set up structured logging configuration"""
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with structured formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(StructuredFormatter())
    
    root_logger.addHandler(console_handler)
    
    # Return application logger
    return logging.getLogger("rag-microservice")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module"""
    return logging.getLogger(f"rag-microservice.{name}")


def log_event(logger: logging.Logger, event_type: str, message: str, **kwargs):
    """Log a structured event with additional context"""
    logger.info(message, extra={"event_type": event_type, **kwargs})


def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None):
    """Log an error with structured context"""
    context = context or {}
    logger.error(
        f"Error occurred: {str(error)}",
        extra={
            "event_type": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            **context
        },
        exc_info=True
    )


def log_request(logger: logging.Logger, method: str, path: str, **kwargs):
    """Log an incoming request"""
    logger.info(
        f"{method} {path}",
        extra={
            "event_type": "request",
            "http_method": method,
            "path": path,
            **kwargs
        }
    )


def log_response(logger: logging.Logger, method: str, path: str, status_code: int, 
                duration_ms: float, **kwargs):
    """Log a response"""
    logger.info(
        f"{method} {path} - {status_code} ({duration_ms:.2f}ms)",
        extra={
            "event_type": "response",
            "http_method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            **kwargs
        }
    )