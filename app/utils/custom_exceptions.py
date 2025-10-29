from fastapi import HTTPException
from typing import Dict, Any, Optional

class DataSummaryAPIException(HTTPException):
    """Base exception class for Data Summary API"""
    def __init__(self, status_code: int, detail: str, error_code: str = None, context: Dict[str, Any] = None):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.context = context or {}

class FileValidationError(DataSummaryAPIException):
    """Raised when file validation fails"""
    def __init__(self, detail: str, context: Dict[str, Any] = None):
        super().__init__(
            status_code=400,
            detail=detail,
            error_code="FILE_VALIDATION_ERROR",
            context=context
        )

class FileSizeError(FileValidationError):
    """Raised when file size exceeds limits"""
    def __init__(self, file_size_mb: float, max_size_mb: int):
        super().__init__(
            detail=f"File size ({file_size_mb:.2f}MB) exceeds maximum allowed size ({max_size_mb}MB)",
            context={
                'file_size_mb': file_size_mb,
                'max_size_mb': max_size_mb,
                'validation_type': 'file_size'
            }
        )

class FileTypeError(FileValidationError):
    """Raised when file type is not supported"""
    def __init__(self, filename: str, detected_type: str, allowed_types: list):
        super().__init__(
            detail=f"File type '{detected_type}' is not supported. Only {', '.join(allowed_types)} files are allowed",
            context={
                'filename': filename,
                'detected_type': detected_type,
                'allowed_types': allowed_types,
                'validation_type': 'file_type'
            }
        )

class DataValidationError(DataSummaryAPIException):
    """Raised when data validation fails"""
    def __init__(self, detail: str, context: Dict[str, Any] = None):
        super().__init__(
            status_code=400,
            detail=detail,
            error_code="DATA_VALIDATION_ERROR",
            context=context
        )

class DataFrameValidationError(DataValidationError):
    """Raised when DataFrame structure validation fails"""
    def __init__(self, detail: str, row_count: int = None, col_count: int = None, min_rows: int = None, max_rows: int = None, min_cols: int = None, max_cols: int = None):
        context = {
            'validation_type': 'dataframe_structure'
        }
        
        if row_count is not None:
            context['row_count'] = row_count
        if col_count is not None:
            context['column_count'] = col_count
        if min_rows is not None:
            context['min_rows_required'] = min_rows
        if max_rows is not None:
            context['max_rows_allowed'] = max_rows
        if min_cols is not None:
            context['min_columns_required'] = min_cols
        if max_cols is not None:
            context['max_columns_allowed'] = max_cols
            
        super().__init__(detail=detail, context=context)

class ColumnValidationError(DataValidationError):
    """Raised when column validation fails"""
    def __init__(self, detail: str, column_name: str = None, column_type: str = None, issue_type: str = None):
        context = {
            'validation_type': 'column_validation'
        }
        
        if column_name:
            context['column_name'] = column_name
        if column_type:
            context['column_type'] = column_type
        if issue_type:
            context['issue_type'] = issue_type
            
        super().__init__(detail=detail, context=context)

class SessionError(DataSummaryAPIException):
    """Raised when session-related operations fail"""
    def __init__(self, detail: str, session_id: str = None, context: Dict[str, Any] = None):
        extra_context = context or {}
        if session_id:
            extra_context['session_id'] = session_id
            
        super().__init__(
            status_code=404,
            detail=detail,
            error_code="SESSION_ERROR",
            context=extra_context
        )

class SessionNotFoundError(SessionError):
    """Raised when session is not found or expired"""
    def __init__(self, session_id: str):
        super().__init__(
            detail="Session not found or expired. Please upload your file again.",
            session_id=session_id,
            context={'error_type': 'session_not_found'}
        )

class DataProcessingError(DataSummaryAPIException):
    """Raised when data processing fails"""
    def __init__(self, detail: str, operation: str = None, context: Dict[str, Any] = None):
        extra_context = context or {}
        if operation:
            extra_context['operation'] = operation
            
        super().__init__(
            status_code=500,
            detail=detail,
            error_code="DATA_PROCESSING_ERROR",
            context=extra_context
        )

class FileReadError(DataProcessingError):
    """Raised when file reading/parsing fails"""
    def __init__(self, filename: str, file_type: str, original_error: str):
        super().__init__(
            detail=f"Failed to read {file_type} file '{filename}'. Please check if the file is valid and not corrupted.",
            operation="file_reading",
            context={
                'filename': filename,
                'file_type': file_type,
                'original_error': str(original_error),
                'error_type': 'file_read_error'
            }
        )

class PlotGenerationError(DataProcessingError):
    """Raised when plot generation fails"""
    def __init__(self, detail: str, column_name: str = None, context: Dict[str, Any] = None):
        extra_context = context or {}
        if column_name:
            extra_context['column_name'] = column_name
            
        super().__init__(
            detail=detail,
            operation="plot_generation",
            context=extra_context
        )
