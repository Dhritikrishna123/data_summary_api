"""
Column metadata and analysis routes
"""
from fastapi import APIRouter, Request, HTTPException, Query
import time
import logging
import pandas as pd
from datetime import datetime, timezone
from app.utils.rate_limiter import limiter
from app.utils.logging_config import log_api_access
from app.utils.custom_exceptions import SessionNotFoundError, ColumnValidationError, DataValidationError

router = APIRouter(prefix='/columns', tags=['columns'])


@router.get("/{session_id}")
@limiter.limit("30/hour")
def get_column_metadata(
    request: Request, 
    session_id: str,
    column: str = Query(None, description="Specific column to analyze (if None, returns all columns")
):
    """
    Get detailed metadata for columns in a session
    """
    start_time = time.time()
    logger = logging.getLogger('data_summary_api')
    
    # Log API access
    client_ip = request.client.host if request.client else "unknown"
    log_api_access(logger, "/columns", "GET", client_ip, session_id)
    
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
        
        # Get column metadata
        if column:
            if column not in df.columns:
                raise ColumnValidationError(
                    detail=f"Column '{column}' not found in dataset. Available columns: {', '.join(df.columns.tolist())}",
                    column_name=column,
                    issue_type='column_not_found'
                )
            metadata = _get_single_column_metadata(df, column)
        else:
            metadata = _get_all_columns_metadata(df)
        
        processing_time = time.time() - start_time
        
        # Log successful metadata generation
        logger.info(
            f"Column metadata generated for session {session_id}",
            extra={'extra_data': {
                'event_type': 'column_metadata_success',
                'session_id': session_id,
                'column_requested': column,
                'total_columns': len(df.columns),
                'processing_time_seconds': round(processing_time, 3)
            }}
        )
        
        try:
            response_data = {
                'session_id': session_id,
                'filename': session['filename'],
                'total_columns': len(df.columns),
                'metadata': metadata,
                'processing_time_seconds': round(processing_time, 3)
            }
            
            # Ensure all values are JSON serializable
            response_data = _ensure_json_serializable(response_data)
            
            return response_data
        except Exception as e:
            logger.error(f"Error creating response: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Error creating response data"
            )
        
    except (SessionNotFoundError, ColumnValidationError, DataValidationError) as e:
        # These are expected errors, just re-raise
        raise e
        
    except Exception as e:
        # Log unexpected errors
        logger.error(
            f"Unexpected error in column metadata generation: {str(e)}",
            extra={'extra_data': {
                'event_type': 'column_metadata_error',
                'session_id': session_id,
                'column_requested': column,
                'error_type': type(e).__name__,
                'error_message': str(e)
            }}
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating column metadata. Please try again."
        )


def _get_single_column_metadata(df: pd.DataFrame, column: str) -> dict:
    """Get detailed metadata for a single column"""
    series = df[column]
    
    metadata = {
        'column_name': column,
        'data_type': str(series.dtype),
        'data_category': series.dtype.kind,
        'total_values': len(series),
        'non_null_count': int(series.count()),
        'null_count': int(series.isna().sum()),
        'null_percentage': round((series.isna().sum() / len(series)) * 100, 2),
        'unique_count': int(series.nunique()),
        'unique_percentage': round((series.nunique() / len(series)) * 100, 2)
    }
    
    # Add type-specific statistics
    if series.dtype.kind in 'biufc':  # numeric types
        metadata.update(_get_numeric_metadata(series))
    else:  # categorical/text types
        metadata.update(_get_categorical_metadata(series))
    
    return metadata


def _get_all_columns_metadata(df: pd.DataFrame) -> dict:
    """Get metadata for all columns"""
    all_metadata = {}
    
    for col in df.columns:
        all_metadata[col] = _get_single_column_metadata(df, col)
    
    return all_metadata


def _get_numeric_metadata(series: pd.Series) -> dict:
    """Get numeric-specific metadata"""
    try:
        numeric_data = series.dropna()
        
        if len(numeric_data) == 0:
            return {
                'min': None,
                'max': None,
                'mean': None,
                'median': None,
                'std': None,
                'percentile_25': None,
                'percentile_75': None,
                'sample_values': []
            }
        
        # Safely convert to Python types
        def safe_float(value):
            if pd.isna(value) or value is None:
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        
        return {
            'min': safe_float(numeric_data.min()),
            'max': safe_float(numeric_data.max()),
            'mean': safe_float(numeric_data.mean()),
            'median': safe_float(numeric_data.median()),
            'std': safe_float(numeric_data.std()),
            'percentile_25': safe_float(numeric_data.quantile(0.25)),
            'percentile_75': safe_float(numeric_data.quantile(0.75)),
            'sample_values': numeric_data.head(5).tolist()
        }
    except Exception as e:
        # Return safe defaults if there's any error
        return {
            'min': None,
            'max': None,
            'mean': None,
            'median': None,
            'std': None,
            'percentile_25': None,
            'percentile_75': None,
            'sample_values': []
        }


def _get_categorical_metadata(series: pd.Series) -> dict:
    """Get categorical-specific metadata"""
    categorical_data = series.dropna()
    
    if len(categorical_data) == 0:
        return {
            'most_common_value': None,
            'most_common_count': 0,
            'value_counts': {},
            'sample_values': []
        }
    
    value_counts = categorical_data.value_counts()
    
    return {
        'most_common_value': str(value_counts.index[0]) if not value_counts.empty else None,
        'most_common_count': int(value_counts.iloc[0]) if not value_counts.empty else 0,
        'value_counts': value_counts.head(10).to_dict(),
        'sample_values': categorical_data.head(5).tolist()
    }


def _ensure_json_serializable(obj):
    """Recursively ensure all values in a dictionary are JSON serializable"""
    import json
    import numpy as np
    import pandas as pd
    
    if isinstance(obj, dict):
        return {key: _ensure_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_ensure_json_serializable(item) for item in obj]
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    else:
        return str(obj)
