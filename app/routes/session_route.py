"""
Session management routes
"""
from fastapi import APIRouter, Request, HTTPException, Query
import time
import logging
import pandas as pd
from datetime import datetime, timezone
from app.utils.rate_limiter import limiter
from app.utils.logging_config import log_api_access
from app.utils.custom_exceptions import SessionNotFoundError

router = APIRouter(prefix='/sessions', tags=['sessions'])


@router.get("/")
@limiter.limit("30/hour")
def list_sessions(request: Request):
    """
    List all active sessions for the current user
    """
    start_time = time.time()
    logger = logging.getLogger('data_summary_api')
    
    # Log API access
    client_ip = request.client.host if request.client else "unknown"
    log_api_access(logger, "/sessions", "GET", client_ip)
    
    try:
        # Get sessions for this client only
        session_security = request.app.state.session_security
        sessions = session_security.get_client_sessions(client_ip)
        session_list = []
        
        for session_data in sessions:
            session_info = {
                'session_id': session_data['session_id'],
                'filename': session_data.get('filename', 'unknown'),
                'filetype': session_data.get('filetype', 'unknown'),
                'upload_time': session_data.get('created_time', datetime.now(timezone.utc)).isoformat(),
                'last_access_time': session_data.get('last_access_time', datetime.now(timezone.utc)).isoformat(),
                'row_count': session_data.get('row_count', 0),
                'column_count': len(session_data.get('df', pd.DataFrame()).columns) if session_data.get('df') is not None else 0,
                'memory_usage_mb': _estimate_memory_usage(session_data.get('df'))
            }
            session_list.append(session_info)
        
        # Sort by upload time (newest first)
        session_list.sort(key=lambda x: x['upload_time'], reverse=True)
        
        processing_time = time.time() - start_time
        
        # Log successful session listing
        logger.info(
            f"Listed {len(session_list)} active sessions",
            extra={'extra_data': {
                'event_type': 'sessions_listed',
                'total_sessions': len(session_list),
                'processing_time_seconds': round(processing_time, 3)
            }}
        )
        
        return {
            'total_sessions': len(session_list),
            'sessions': session_list,
            'processing_time_seconds': round(processing_time, 3)
        }
        
    except Exception as e:
        logger.error(
            f"Error listing sessions: {str(e)}",
            extra={'extra_data': {
                'event_type': 'sessions_list_error',
                'error_type': type(e).__name__,
                'error_message': str(e)
            }}
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while listing sessions. Please try again."
        )


@router.delete("/{session_id}")
@limiter.limit("20/hour")
def delete_session(request: Request, session_id: str):
    """
    Delete a specific session
    """
    start_time = time.time()
    logger = logging.getLogger('data_summary_api')
    
    # Log API access
    client_ip = request.client.host if request.client else "unknown"
    log_api_access(logger, "/sessions", "DELETE", client_ip, session_id)
    
    try:
        # Use secure session system
        session_security = request.app.state.session_security
        
        # Check if session exists and client has access
        session_data = session_security.get_session(session_id, client_ip)
        if not session_data:
            raise SessionNotFoundError(session_id)
        
        filename = session_data.get('filename', 'unknown')
        row_count = session_data.get('row_count', 0)
        
        # Delete session (only if client has access)
        if not session_security.delete_session(session_id, client_ip):
            raise SessionNotFoundError(session_id)
        
        processing_time = time.time() - start_time
        
        # Log successful session deletion
        logger.info(
            f"Session {session_id} deleted successfully",
            extra={'extra_data': {
                'event_type': 'session_deleted',
                'session_id': session_id,
                'filename': filename,
                'row_count': row_count,
                'processing_time_seconds': round(processing_time, 3)
            }}
        )
        
        return {
            'message': f'Session {session_id} deleted successfully',
            'session_id': session_id,
            'filename': filename,
            'processing_time_seconds': round(processing_time, 3)
        }
        
    except SessionNotFoundError as e:
        # Re-raise session not found errors
        raise e
        
    except Exception as e:
        logger.error(
            f"Error deleting session {session_id}: {str(e)}",
            extra={'extra_data': {
                'event_type': 'session_delete_error',
                'session_id': session_id,
                'error_type': type(e).__name__,
                'error_message': str(e)
            }}
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while deleting the session. Please try again."
        )


def _estimate_memory_usage(df) -> float:
    """Estimate memory usage of DataFrame in MB"""
    try:
        if df is None or df.empty:
            return 0.0
        memory_usage = df.memory_usage(deep=True).sum()
        return round(memory_usage / (1024 * 1024), 2)
    except Exception:
        return 0.0
