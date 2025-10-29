from fastapi import HTTPException, APIRouter, Request, Query
import time
import logging
from datetime import datetime, timezone
from app.utils.rate_limiter import limiter
from app.utils.logging_config import log_api_access
from app.utils.custom_exceptions import SessionNotFoundError, DataProcessingError, DataValidationError
from app.processors.data_analyzer import (
    compute_numeric_summary, 
    compute_categorical_summary, 
    compute_correlation_matrix, 
    compute_data_quality_metrics
)
from app.builders.response_builder import build_summary_response

router = APIRouter(prefix='/summary', tags=['summary'])


@router.get(
    "/",
    summary="Get Data Summary Statistics",
    description="Generate comprehensive statistical summary of the dataset including numeric statistics, categorical analysis, correlation matrix, and data quality metrics.",
    response_description="Returns detailed statistical summary of the dataset",
    responses={
        200: {
            "description": "Summary generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "filename": "data.csv",
                        "filetype": "CSV",
                        "row_count": 1000,
                        "column_count": 5,
                        "numeric_columns": 2,
                        "categorical_columns": 3,
                        "summary": {
                            "numeric_summary": {
                                "age": {
                                    "mean": 35.5,
                                    "median": 35.0,
                                    "std": 8.2,
                                    "min": 22,
                                    "max": 65,
                                    "count": 1000,
                                    "missing": 0,
                                    "percent_missing": 0.0,
                                    "percentile_25": 29.0,
                                    "percentile_75": 42.0
                                }
                            },
                            "categorical_summary": {
                                "department": {
                                    "unique_count": 5,
                                    "most_common_value": "Engineering",
                                    "most_common_count": 300,
                                    "data_type": "object"
                                }
                            },
                            "correlation_matrix": {
                                "columns": ["age", "salary"],
                                "correlation_matrix": {
                                    "age": {"age": 1.0, "salary": 0.75},
                                    "salary": {"age": 0.75, "salary": 1.0}
                                }
                            },
                            "data_quality": {
                                "age": {
                                    "total_values": 1000,
                                    "missing_values": 0,
                                    "percent_missing": 0.0,
                                    "data_quality": "excellent"
                                }
                            }
                        },
                        "warnings": [],
                        "processing_time_seconds": 0.156
                    }
                }
            }
        },
        404: {
            "description": "Session not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Session 'invalid-session-id' not found"
                    }
                }
            }
        },
        400: {
            "description": "Invalid columns specified",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Columns not found: invalid_column"
                    }
                }
            }
        }
    }
)
@limiter.limit("20/hour")
def get_summary(
    request: Request, 
    session_id: str = Query(..., description='Unique session id for the uploaded file'),
    include_categorical: bool = Query(False, description='Include statistics for categorical columns'),
    include_correlation: bool = Query(False, description='Include correlation matrix for numeric columns'),
    include_quality: bool = Query(False, description='Include data quality metrics'),
    columns: str = Query(None, description='Comma-separated list of specific columns to analyze')
):
    start_time = time.time()
    logger = logging.getLogger('data_summary_api')
    
    # Log API access
    client_ip = request.client.host if request.client else "unknown"
    log_api_access(logger, "/summary", "GET", client_ip, session_id)
    
    try:
        # Use secure session system
        session_security = request.app.state.session_security
        session = session_security.get_session(session_id, client_ip)
        if not session:
            raise SessionNotFoundError(session_id)

        df = session.get('df')
        
        if df is None or df.empty:
            raise DataValidationError(
                detail="Uploaded file is empty or invalid. Please upload a valid file with data.",
                context={'validation_type': 'empty_dataframe', 'session_id': session_id}
            )

        # Filter columns if specified
        if columns:
            column_list = [col.strip() for col in columns.split(',')]
            missing_cols = [col for col in column_list if col not in df.columns]
            if missing_cols:
                raise DataValidationError(
                    detail=f"Columns not found: {', '.join(missing_cols)}",
                    context={'validation_type': 'missing_columns', 'missing_columns': missing_cols}
                )
            df = df[column_list]
        
        # Compute enhanced summary statistics
        summary_data = {
            'numeric_summary': compute_numeric_summary(df)
        }
        
        if include_categorical:
            summary_data['categorical_summary'] = compute_categorical_summary(df)
        
        if include_correlation:
            summary_data['correlation_matrix'] = compute_correlation_matrix(df)
        
        if include_quality:
            summary_data['data_quality'] = compute_data_quality_metrics(df)
        
        processing_time = time.time() - start_time
        
        # Log successful summary generation
        logger.info(
            f"Summary generated for session {session_id}",
            extra={'extra_data': {
                'event_type': 'summary_success',
                'session_id': session_id,
                'filename': session['filename'],
                'numeric_columns': len(summary_data['numeric_summary']),
                'total_columns': len(df.columns),
                'include_categorical': include_categorical,
                'include_correlation': include_correlation,
                'include_quality': include_quality,
                'processing_time_seconds': round(processing_time, 3)
            }}
        )
        
        # Build and return response using modular builder
        return build_summary_response(session, summary_data, processing_time)
        
    except (SessionNotFoundError, DataValidationError) as e:
        # These are expected errors, just re-raise
        raise e
        
    except Exception as e:
        # Log unexpected errors
        logger.error(
            f"Unexpected error in summary generation: {str(e)}",
            extra={'extra_data': {
                'event_type': 'summary_error',
                'session_id': session_id,
                'error_type': type(e).__name__,
                'error_message': str(e)
            }}
        )
        raise DataProcessingError(
            detail="An error occurred while generating the summary. Please try again.",
            operation="summary_generation",
            context={'session_id': session_id, 'original_error': str(e)}
        )
