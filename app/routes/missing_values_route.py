"""
Missing values analysis and handling routes
"""
from fastapi import APIRouter, Request, HTTPException, Query
import time
import logging
import pandas as pd
from datetime import datetime, timezone
from app.utils.rate_limiter import limiter
from app.utils.logging_config import log_api_access
from app.utils.custom_exceptions import SessionNotFoundError, DataValidationError
from app.handlers.missing_value_handler import (
    get_missing_value_report, 
    get_missing_value_statistics,
    handle_missing_values
)

router = APIRouter(prefix='/missing-values', tags=['missing-values'])


@router.get("/{session_id}")
@limiter.limit("20/hour")
def get_missing_value_report_endpoint(
    request: Request, 
    session_id: str
):
    """
    Get comprehensive missing value report for a session
    """
    start_time = time.time()
    logger = logging.getLogger('data_summary_api')
    
    # Log API access
    client_ip = request.client.host if request.client else "unknown"
    log_api_access(logger, "/missing-values", "GET", client_ip, session_id)
    
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
        
        # Generate missing value report
        report = get_missing_value_report(df)
        statistics = get_missing_value_statistics(df)
        
        processing_time = time.time() - start_time
        
        # Log successful report generation
        logger.info(
            f"Missing value report generated for session {session_id}",
            extra={'extra_data': {
                'event_type': 'missing_values_report_success',
                'session_id': session_id,
                'columns_with_missing': len(report['columns_with_missing']),
                'processing_time_seconds': round(processing_time, 3)
            }}
        )
        
        return {
            'session_id': session_id,
            'filename': session['filename'],
            'report': report,
            'statistics': statistics,
            'processing_time_seconds': round(processing_time, 3)
        }
        
    except (SessionNotFoundError, DataValidationError) as e:
        # These are expected errors, just re-raise
        raise e
        
    except Exception as e:
        # Log unexpected errors
        logger.error(
            f"Unexpected error in missing value report generation: {str(e)}",
            extra={'extra_data': {
                'event_type': 'missing_values_report_error',
                'session_id': session_id,
                'error_type': type(e).__name__,
                'error_message': str(e)
            }}
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating the missing value report. Please try again."
        )


@router.post("/{session_id}/handle")
@limiter.limit("10/hour")
def handle_missing_values_endpoint(
    request: Request, 
    session_id: str,
    strategy: str = Query(..., description="Strategy to handle missing values: skip, fill_mean, fill_median, fill_mode, forward_fill, backward_fill"),
    columns: str = Query(None, description="Comma-separated list of columns to process (if None, processes all columns)")
):
    """
    Handle missing values in a session with specified strategy
    """
    start_time = time.time()
    logger = logging.getLogger('data_summary_api')
    
    # Log API access
    client_ip = request.client.host if request.client else "unknown"
    log_api_access(logger, "/missing-values/handle", "POST", client_ip, session_id)
    
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
        
        # Parse columns parameter
        columns_list = None
        if columns:
            columns_list = [col.strip() for col in columns.split(',')]
            missing_cols = [col for col in columns_list if col not in df.columns]
            if missing_cols:
                raise HTTPException(
                    status_code=400,
                    detail=f"Columns not found: {', '.join(missing_cols)}"
                )
        
        # Get original statistics
        original_stats = get_missing_value_statistics(df)
        
        # Handle missing values
        df_processed = handle_missing_values(df, strategy, columns_list)
        
        # Update session with processed data
        session['df'] = df_processed
        session['row_count'] = len(df_processed)
        
        # Get processed statistics
        processed_stats = get_missing_value_statistics(df_processed)
        
        processing_time = time.time() - start_time
        
        # Log successful missing value handling
        logger.info(
            f"Missing values handled for session {session_id}",
            extra={'extra_data': {
                'event_type': 'missing_values_handled',
                'session_id': session_id,
                'strategy': strategy,
                'columns_processed': columns_list or 'all',
                'original_missing_cells': original_stats['overall']['missing_cells'],
                'processed_missing_cells': processed_stats['overall']['missing_cells'],
                'processing_time_seconds': round(processing_time, 3)
            }}
        )
        
        return {
            'message': f'Missing values handled successfully using {strategy} strategy',
            'session_id': session_id,
            'strategy': strategy,
            'columns_processed': columns_list or 'all',
            'original_statistics': original_stats,
            'processed_statistics': processed_stats,
            'processing_time_seconds': round(processing_time, 3)
        }
        
    except (SessionNotFoundError, DataValidationError) as e:
        # These are expected errors, just re-raise
        raise e
        
    except Exception as e:
        # Log unexpected errors
        logger.error(
            f"Unexpected error in missing value handling: {str(e)}",
            extra={'extra_data': {
                'event_type': 'missing_values_handle_error',
                'session_id': session_id,
                'strategy': strategy,
                'error_type': type(e).__name__,
                'error_message': str(e)
            }}
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while handling missing values. Please try again."
        )
