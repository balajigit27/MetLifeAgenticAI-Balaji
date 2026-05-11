"""
Structured logging utility for production-ready output.

Features:
- JSON logging for production environments
- Colored console output for development
- Contextual logging with task IDs
- Performance metrics logging
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from config import settings


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        # Add custom fields
        if hasattr(record, "task_id"):
            log_obj["task_id"] = record.task_id
        if hasattr(record, "duration_ms"):
            log_obj["duration_ms"] = record.duration_ms
        
        return json.dumps(log_obj)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for development."""

    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # Format the basic message
        log_msg = f"{color}[{record.levelname:8s}]{self.RESET} {record.name:20s} | {record.getMessage()}"
        
        # Add timing information if available
        if hasattr(record, "duration_ms"):
            log_msg += f" ({record.duration_ms:.0f}ms)"
        
        # Add exception if present
        if record.exc_info:
            log_msg += f"\n{self.formatException(record.exc_info)}"
        
        return log_msg


def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for file logging
        
    Returns:
        Configured logger instance
        
    Example:
        logger = setup_logger(__name__)
        logger.info("Starting research")
        logger.error("Failed to fetch URL", extra={"task_id": "task-123"})
    """
    level = level or settings.log_level
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level))
    
    if settings.json_logging:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ColoredFormatter())
    
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level))
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


class LogContext:
    """Context manager for adding contextual information to logs."""
    
    def __init__(self, logger: logging.Logger, task_id: str, **extra):
        """
        Initialize log context.
        
        Args:
            logger: Logger instance
            task_id: Unique task identifier
            **extra: Additional context fields
        """
        self.logger = logger
        self.task_id = task_id
        self.extra = extra
        self.start_time = None
    
    def __enter__(self):
        """Enter context."""
        self.start_time = datetime.utcnow()
        self.logger.info(
            f"Starting task: {self.task_id}",
            extra={"task_id": self.task_id, **self.extra}
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and log duration."""
        duration_ms = (datetime.utcnow() - self.start_time).total_seconds() * 1000
        
        if exc_type is None:
            self.logger.info(
                f"Completed task: {self.task_id}",
                extra={
                    "task_id": self.task_id,
                    "duration_ms": duration_ms,
                    **self.extra
                }
            )
        else:
            self.logger.error(
                f"Failed task: {self.task_id} - {exc_val}",
                exc_info=(exc_type, exc_val, exc_tb),
                extra={
                    "task_id": self.task_id,
                    "duration_ms": duration_ms,
                    **self.extra
                }
            )


# Global logger instance
logger = setup_logger(__name__)


if __name__ == "__main__":
    # Quick test
    test_logger = setup_logger("test", level="DEBUG")
    test_logger.debug("Debug message")
    test_logger.info("Info message")
    test_logger.warning("Warning message")
    test_logger.error("Error message")
    
    # Test context
    with LogContext(test_logger, "test-task-001", source="test"):
        test_logger.info("Inside context")
