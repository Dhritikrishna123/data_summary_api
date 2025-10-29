import logging
import sys
from datetime import datetime
from typing import Dict, Any
import json

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
            
        return json.dumps(log_entry)

def setup_logging():
    """Configure application logging"""
    
    # Create logger
    logger = logging.getLogger('data_summary_api')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler with structured formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(StructuredFormatter())
    
    # File handler for errors
    file_handler = logging.FileHandler('app.log', mode='a')
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(StructuredFormatter())
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Prevent duplicate logs
    logger.propagate = False
    
    return logger

def log_upload_success(logger: logging.Logger, filename: str, file_size: int, row_count: int, col_count: int, filetype: str, session_id: str, processing_time: float):
    """Log successful file upload"""
    logger.info(
        f"File uploaded successfully: {filename}",
        extra={
            'extra_data': {
                'event_type': 'upload_success',
                'filename': filename,
                'file_size_bytes': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'row_count': row_count,
                'column_count': col_count,
                'filetype': filetype,
                'session_id': session_id,
                'processing_time_seconds': round(processing_time, 3)
            }
        }
    )

def log_upload_error(logger: logging.Logger, filename: str, error_type: str, error_message: str, file_size: int = None):
    """Log file upload errors"""
    extra_data = {
        'event_type': 'upload_error',
        'filename': filename,
        'error_type': error_type,
        'error_message': error_message
    }
    
    if file_size:
        extra_data['file_size_bytes'] = file_size
        extra_data['file_size_mb'] = round(file_size / (1024 * 1024), 2)
    
    logger.error(
        f"File upload failed: {filename} - {error_type}",
        extra={'extra_data': extra_data}
    )

def log_api_access(logger: logging.Logger, endpoint: str, method: str, client_ip: str, session_id: str = None, response_time: float = None):
    """Log API access patterns"""
    extra_data = {
        'event_type': 'api_access',
        'endpoint': endpoint,
        'method': method,
        'client_ip': client_ip,
        'response_time_ms': round(response_time * 1000, 2) if response_time else None
    }
    
    if session_id:
        extra_data['session_id'] = session_id
    
    logger.info(
        f"API access: {method} {endpoint}",
        extra={'extra_data': extra_data}
    )

