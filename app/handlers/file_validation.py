"""
File validation handlers for upload operations
"""
from fastapi import HTTPException
from app.utils.custom_exceptions import FileValidationError, FileSizeError, FileTypeError
from app.utils.files_validation import validate_size, validate_file_type


def validate_upload_file(file, contents: bytes) -> None:
    """
    Comprehensive file validation for uploads
    
    Args:
        file: UploadFile object
        contents: File contents as bytes
        
    Raises:
        FileValidationError: For general validation failures
        FileSizeError: For file size violations
        FileTypeError: For unsupported file types
    """
    # Basic file validation
    if not file.filename or not file.filename.strip():
        raise FileValidationError("No filename provided")
    
    # Check file extension
    if not file.filename.lower().endswith(('.csv', '.xlsx')):
        raise FileTypeError(
            filename=file.filename,
            detected_type=file.filename.split('.')[-1].upper() if '.' in file.filename else 'unknown',
            allowed_types=['CSV', 'XLSX']
        )
    
    # Validate file size
    try:
        validate_size(contents)
    except HTTPException as e:
        raise FileSizeError(
            file_size_mb=len(contents) / (1024 * 1024),
            max_size_mb=60
        )
    
    # Validate file type using magic
    try:
        validate_file_type(contents)
    except HTTPException as e:
        raise FileTypeError(
            filename=file.filename,
            detected_type="unknown",
            allowed_types=['CSV', 'XLSX']
        )
