"""
Response builders for consistent API responses
"""
from datetime import datetime, timezone
from typing import Dict, Any
import pandas as pd


def build_upload_response(
    df: pd.DataFrame,
    filename: str,
    filetype: str,
    session_id: str,
    processing_time: float,
    memory_estimate: Dict[str, Any],
    data_types_summary: Dict[str, Any],
    include_sample: bool = False
) -> Dict[str, Any]:
    """Build enhanced upload response"""
    row_count, col_count = df.shape
    
    response_data = {
        'message': 'File uploaded successfully',
        'session_id': session_id,
        'filename': filename,
        'filetype': filetype,
        'metadata': {
            'row_count': row_count,
            'column_count': col_count,
            'columns': df.columns.tolist(),
            'memory_estimate': memory_estimate,
            'data_types': data_types_summary,
            'processing_time_seconds': round(processing_time, 3)
        }
    }
    
    # Add sample data if requested
    if include_sample:
        from app.processors.data_analyzer import get_sample_data
        sample_data = get_sample_data(df)
        response_data['sample_data'] = sample_data
    
    return response_data


def build_summary_response(
    session: Dict[str, Any],
    summary_data: Dict[str, Any],
    processing_time: float
) -> Dict[str, Any]:
    """Build enhanced summary response"""
    df = session.get('df')
    numeric_cols = df.select_dtypes(include=['number']).columns if df is not None else []
    categorical_cols = df.select_dtypes(exclude=['number']).columns if df is not None else []
    
    response = {
        "filename": session['filename'],
        "filetype": session['filetype'],
        "row_count": session['row_count'],
        "column_count": len(df.columns) if df is not None else 0,
        "numeric_columns": len(numeric_cols),
        "categorical_columns": len(categorical_cols),
        "summary": summary_data,
        "processing_time_seconds": round(processing_time, 3)
    }
    
    # Add warnings for high missing percentages
    if 'data_quality' in summary_data:
        warnings = []
        for col, metrics in summary_data['data_quality'].items():
            if metrics['percent_missing'] > 50:
                warnings.append(f"Column '{col}' has {metrics['percent_missing']}% missing values")
        if warnings:
            response['warnings'] = warnings
    
    return response


def create_session_data(
    df: pd.DataFrame,
    filename: str,
    filetype: str
) -> Dict[str, Any]:
    """Create session data structure"""
    return {
        'df': df,
        'filename': filename,
        'filetype': filetype,
        'upload_time': datetime.now(timezone.utc),
        'row_count': len(df),
        'last_access_time': datetime.now(timezone.utc)
    }
