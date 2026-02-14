"""Structured JSON logging configuration."""

import json
import logging
import sys
from datetime import datetime
from typing import Any

from app.core.metrics_config import should_log


class SectionFilter(logging.Filter):
    """Filter log records based on section-specific configuration."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records based on section and level configuration.
        
        Args:
            record: Log record to filter
            
        Returns:
            True if the record should be logged, False otherwise
        """
        # Determine section from logger name or module
        section = "unknown"
        if "document" in record.name.lower() or "extraction" in record.name.lower():
            section = "document_processing"
        elif "chat" in record.name.lower():
            section = "chat"
        elif "validation" in record.name.lower():
            section = "validation"
        elif "chaser" in record.name.lower() or "email" in record.name.lower():
            section = "email"
        elif "api" in record.name.lower():
            section = "api"
        elif "ai" in record.name.lower():
            section = "ai"
        
        # Store section on the record for use by formatter
        record.section = section
        
        # Check if logging is enabled for this section and level
        return should_log(section, record.levelno)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Get section from record (set by SectionFilter)
        section = getattr(record, "section", "unknown")
        
        # Format source location
        source = f"{record.module}:{record.funcName}"
        
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "section": section,
            "source": source,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            log_data["stack_trace"] = self.formatStack(record.stack_info) if record.stack_info else None
        
        # Add extra fields from record (may override section/source if provided)
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        # Add request ID if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        return json.dumps(log_data, default=str)


def setup_structured_logging(debug: bool = False) -> None:
    """Setup structured JSON logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    root_logger.handlers.clear()
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_handler.setFormatter(JSONFormatter())
    
    # Add section-based filter to handler
    section_filter = SectionFilter()
    console_handler.addFilter(section_filter)
    
    root_logger.addHandler(console_handler)
    
    # Configure log levels
    logging.getLogger("app").setLevel(logging.DEBUG if debug else logging.INFO)
    logging.getLogger("app.ai").setLevel(logging.INFO)  # Always log AI calls
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    
    logging.info("Structured logging configured successfully")
