"""
Data export routes
"""
from fastapi import APIRouter, Request, HTTPException, Query, Response
import time
import logging
import pandas as pd
import io
import json
from datetime import datetime, timezone
from app.utils.rate_limiter import limiter
from app.utils.logging_config import log_api_access
from app.utils.custom_exceptions import SessionNotFoundError, DataValidationError

router = APIRouter(prefix='/export', tags=['export'])


@router.get("/{session_id}")
@limiter.limit("10/hour")
def export_data(
    request: Request, 
    session_id: str,
    format: str = Query("csv", description="Export format: csv or json"),
    columns: str = Query(None, description="Comma-separated list of columns to export (if None, exports all columns)"),
    rows: int = Query(None, description="Number of rows to export (if None, exports all rows)")
):
    """
    Export processed data in CSV or JSON format
    """
    start_time = time.time()
    logger = logging.getLogger('data_summary_api')
    
    # Log API access
    client_ip = request.client.host if request.client else "unknown"
    log_api_access(logger, "/export", "GET", client_ip, session_id)
    
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
                raise HTTPException(
                    status_code=400,
                    detail=f"Columns not found: {', '.join(missing_cols)}"
                )
            df_export = df[column_list]
        else:
            df_export = df
        
        # Filter rows if specified
        if rows and rows > 0:
            df_export = df_export.head(rows)
        
        # Generate export based on format
        if format.lower() == 'csv':
            return _export_csv(df_export, session['filename'], session_id)
        elif format.lower() == 'json':
            return _export_json(df_export, session['filename'], session_id)
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid format. Supported formats: csv, json"
            )
        
    except (SessionNotFoundError, DataValidationError) as e:
        # These are expected errors, just re-raise
        raise e
        
    except Exception as e:
        # Log unexpected errors
        logger.error(
            f"Unexpected error in data export: {str(e)}",
            extra={'extra_data': {
                'event_type': 'export_error',
                'session_id': session_id,
                'format': format,
                'error_type': type(e).__name__,
                'error_message': str(e)
            }}
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while exporting data. Please try again."
        )


def _export_csv(df: pd.DataFrame, filename: str, session_id: str) -> Response:
    """Export DataFrame as CSV"""
    try:
        # Create CSV content
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        csv_content = csv_buffer.getvalue()
        csv_buffer.close()
        
        # Create filename
        base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        export_filename = f"{base_name}_export.csv"
        
        # Log successful export
        logger = logging.getLogger('data_summary_api')
        logger.info(
            f"Data exported as CSV for session {session_id}",
            extra={'extra_data': {
                'event_type': 'export_success',
                'session_id': session_id,
                'format': 'csv',
                'rows_exported': len(df),
                'columns_exported': len(df.columns)
            }}
        )
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={export_filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export CSV: {str(e)}"
        )


def _export_json(df: pd.DataFrame, filename: str, session_id: str) -> Response:
    """Export DataFrame as JSON"""
    try:
        # Convert DataFrame to JSON
        json_content = df.to_json(orient='records', date_format='iso', indent=2)
        
        # Create filename
        base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        export_filename = f"{base_name}_export.json"
        
        # Log successful export
        logger = logging.getLogger('data_summary_api')
        logger.info(
            f"Data exported as JSON for session {session_id}",
            extra={'extra_data': {
                'event_type': 'export_success',
                'session_id': session_id,
                'format': 'json',
                'rows_exported': len(df),
                'columns_exported': len(df.columns)
            }}
        )
        
        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={export_filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export JSON: {str(e)}"
        )
