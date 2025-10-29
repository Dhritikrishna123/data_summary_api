from fastapi import APIRouter, File, UploadFile, HTTPException, Request, Query
import uuid
import time
import logging
from app.utils.rate_limiter import limiter
from app.utils.logging_config import log_upload_success, log_upload_error, log_api_access
from app.utils.custom_exceptions import (
    FileSizeError, FileTypeError, FileReadError, DataFrameValidationError,
    FileValidationError, DataValidationError
)
from app.handlers.file_validation import validate_upload_file
from app.handlers.file_parser import parse_file_contents
from app.processors.data_analyzer import get_memory_usage_estimate, get_data_types_summary
from app.builders.response_builder import build_upload_response, create_session_data

router = APIRouter(prefix="/upload", tags=['Upload'])


@router.post(
    "/",
    summary="Upload Data File",
    description="Upload a CSV or Excel file for data analysis. The API supports automatic encoding detection for CSV files and provides comprehensive metadata about the uploaded dataset.",
    response_description="Returns session information and dataset metadata",
    responses={
        200: {
            "description": "File uploaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "File uploaded successfully",
                        "session_id": "123e4567-e89b-12d3-a456-426614174000",
                        "filename": "data.csv",
                        "filetype": "CSV",
                        "metadata": {
                            "row_count": 1000,
                            "column_count": 5,
                            "columns": ["name", "age", "salary", "department", "hire_date"],
                            "memory_estimate": {
                                "total_bytes": 1048576,
                                "total_mb": 1.0
                            },
                            "data_types": {
                                "name": {"dtype": "object", "unique_count": 1000},
                                "age": {"dtype": "int64", "unique_count": 45}
                            },
                            "processing_time_seconds": 0.245
                        }
                    }
                }
            }
        },
        400: {
            "description": "Invalid file or file too large",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "File size exceeds maximum limit of 100MB"
                    }
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An unexpected error occurred while processing the file. Please try again."
                    }
                }
            }
        }
    }
)
@limiter.limit("20/hour")
async def upload_file(
    request: Request, 
    file: UploadFile = File(..., description="CSV or Excel file to upload"),
    include_sample: bool = Query(False, description="Include sample data in response"),
    encoding: str = Query(None, description="File encoding for CSV files (auto-detected if not specified)")
):
    start_time = time.time()
    logger = logging.getLogger('data_summary_api')
    
    # Log API access
    client_ip = request.client.host if request.client else "unknown"
    log_api_access(logger, "/upload", "POST", client_ip)
    
    try:
        # Read file contents
        contents = await file.read()
        file_size = len(contents)
        
        # Validate file
        validate_upload_file(file, contents)
        
        # Parse file contents with encoding support
        df, filetype = parse_file_contents(file.filename, contents, encoding)
        
        # Create secure session
        session_security = request.app.state.session_security
        session_id = session_security.create_session(client_ip, file.filename, filetype)
        row_count, col_count = df.shape
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Get enhanced metadata
        memory_estimate = get_memory_usage_estimate(df)
        data_types_summary = get_data_types_summary(df)
        
        # Update session with data
        session_security.update_session(
            session_id, 
            client_ip,
            df=df,
            row_count=row_count,
            column_count=col_count,
            memory_estimate=memory_estimate,
            data_types_summary=data_types_summary
        )
        
        # Log successful upload
        log_upload_success(
            logger=logger,
            filename=file.filename,
            file_size=file_size,
            row_count=row_count,
            col_count=col_count,
            filetype=filetype,
            session_id=session_id,
            processing_time=processing_time
        )
        
        # Build and return response
        return build_upload_response(
            df=df,
            filename=file.filename,
            filetype=filetype,
            session_id=session_id,
            processing_time=processing_time,
            memory_estimate=memory_estimate,
            data_types_summary=data_types_summary,
            include_sample=include_sample
        )
        
    except (FileValidationError, FileTypeError, FileSizeError, FileReadError, 
            DataFrameValidationError, DataValidationError) as e:
        # Log validation/processing errors
        log_upload_error(
            logger=logger,
            filename=getattr(file, 'filename', 'unknown'),
            error_type=e.error_code if hasattr(e, 'error_code') else type(e).__name__,
            error_message=str(e.detail),
            file_size=getattr(e, 'context', {}).get('file_size_bytes') if hasattr(e, 'context') else None
        )
        raise e
        
    except Exception as e:
        # Log unexpected errors
        log_upload_error(
            logger=logger,
            filename=getattr(file, 'filename', 'unknown'),
            error_type='UNEXPECTED_ERROR',
            error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the file. Please try again."
        )