"""
Session security utilities for data isolation
"""
import secrets
import hashlib
import time
from datetime import datetime, timezone
from typing import Dict, Optional
import logging

class SessionSecurity:
    """Handles session security and data isolation"""
    
    def __init__(self):
        self.sessions = {}  # session_id -> session_data
        self.client_sessions = {}  # client_ip -> [session_ids]
        self.logger = logging.getLogger('data_summary_api')
    
    def create_session(self, client_ip: str, filename: str, filetype: str) -> str:
        """Create a new secure session"""
        # Generate cryptographically secure session ID
        session_id = secrets.token_urlsafe(32)
        
        # Create session data
        session_data = {
            'session_id': session_id,
            'client_ip': client_ip,
            'filename': filename,
            'filetype': filetype,
            'created_time': datetime.now(timezone.utc),
            'last_access_time': datetime.now(timezone.utc),
            'df': None,  # Will be set when file is processed
            'row_count': 0,
            'column_count': 0
        }
        
        # Store session
        self.sessions[session_id] = session_data
        
        # Track client sessions
        if client_ip not in self.client_sessions:
            self.client_sessions[client_ip] = []
        self.client_sessions[client_ip].append(session_id)
        
        self.logger.info(
            f"Created secure session {session_id} for client {client_ip}",
            extra={'extra_data': {
                'event_type': 'session_created',
                'session_id': session_id,
                'client_ip': client_ip,
                'filename': filename
            }}
        )
        
        return session_id
    
    def get_session(self, session_id: str, client_ip: str) -> Optional[Dict]:
        """Get session data if client has access"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check if client has access to this session
        if session['client_ip'] != client_ip:
            self.logger.warning(
                f"Unauthorized access attempt to session {session_id} from {client_ip}",
                extra={'extra_data': {
                    'event_type': 'unauthorized_access',
                    'session_id': session_id,
                    'client_ip': client_ip,
                    'session_owner': session['client_ip']
                }}
            )
            return None
        
        # Update last access time
        session['last_access_time'] = datetime.now(timezone.utc)
        return session
    
    def update_session(self, session_id: str, client_ip: str, **updates) -> bool:
        """Update session data if client has access"""
        session = self.get_session(session_id, client_ip)
        if not session:
            return False
        
        # Update session data
        for key, value in updates.items():
            session[key] = value
        
        return True
    
    def delete_session(self, session_id: str, client_ip: str) -> bool:
        """Delete session if client has access"""
        session = self.get_session(session_id, client_ip)
        if not session:
            return False
        
        # Remove from sessions
        del self.sessions[session_id]
        
        # Remove from client sessions
        if client_ip in self.client_sessions:
            try:
                self.client_sessions[client_ip].remove(session_id)
            except ValueError:
                pass
        
        self.logger.info(
            f"Deleted session {session_id} by client {client_ip}",
            extra={'extra_data': {
                'event_type': 'session_deleted',
                'session_id': session_id,
                'client_ip': client_ip
            }}
        )
        
        return True
    
    def get_client_sessions(self, client_ip: str) -> list:
        """Get all sessions for a specific client"""
        if client_ip not in self.client_sessions:
            return []
        
        # Filter out expired sessions
        valid_sessions = []
        for session_id in self.client_sessions[client_ip]:
            if session_id in self.sessions:
                valid_sessions.append(self.sessions[session_id])
        
        return valid_sessions
    
    def get_total_sessions(self) -> int:
        """Get total number of active sessions across all clients"""
        return len(self.sessions)
    
    def cleanup_expired_sessions(self, expiry_seconds: int = 3600):
        """Clean up expired sessions"""
        now = datetime.now(timezone.utc)
        expired = []
        
        for session_id, session in list(self.sessions.items()):
            if (now - session['last_access_time']).total_seconds() > expiry_seconds:
                expired.append(session_id)
        
        # Remove expired sessions
        for session_id in expired:
            session = self.sessions[session_id]
            client_ip = session['client_ip']
            
            # Remove from client sessions
            if client_ip in self.client_sessions:
                try:
                    self.client_sessions[client_ip].remove(session_id)
                except ValueError:
                    pass
            
            del self.sessions[session_id]
            
            self.logger.info(
                f"Cleaned up expired session {session_id}",
                extra={'extra_data': {
                    'event_type': 'session_cleanup',
                    'session_id': session_id,
                    'client_ip': client_ip,
                    'age_seconds': int((now - session['created_time']).total_seconds())
                }}
            )
    
    def validate_session_access(self, session_id: str, client_ip: str) -> bool:
        """Validate if client has access to session"""
        return self.get_session(session_id, client_ip) is not None

# Global session security instance
session_security = SessionSecurity()
