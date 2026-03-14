"""Structured logging configuration for MihenkAI."""
import logging
import sys
import json
from logging import LogRecord
from pythonjsonlogger import jsonlogger


# Custom JSON encoder for log records
class JSONEncoder(json.JSONEncoder):
    """JSON encoder that handles special types."""
    
    def default(self, obj):
        """Convert objects to JSON-serializable form."""
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        if isinstance(obj, Exception):
            return str(obj)
        return str(obj)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""
    
    def add_fields(self, log_record: dict, record: LogRecord, message_dict: dict) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Add custom fields
        log_record['timestamp'] = self.formatTime(record)
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        
        # Add source location
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add process and thread info
        log_record['process_id'] = record.process
        log_record['thread_id'] = record.thread
        
        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)


def setup_logging(env: str = "development", log_level: str = "INFO"):
    """Setup structured logging for the application.
    
    Args:
        env: Environment name ('development', 'production')
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    if env == "production":
        # JSON structured logging for production
        formatter = CustomJsonFormatter(
            '%(message)s %(exception)s',
            json_encoder=JSONEncoder,
            static_fields={
                'environment': env,
                'service': 'mihenkai'
            }
        )
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Suppress noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
