from datetime import datetime, timezone
import time
import logging

def cleanup_expired_sessions(app, expiry_seconds=3600, interval_seconds=600):
    """Background thread that periodically removes expired sessions."""
    logger = logging.getLogger('data_summary_api')
    
    while True:
        try:
            # Use the secure session system
            if hasattr(app.state, 'session_security'):
                app.state.session_security.cleanup_expired_sessions(expiry_seconds)
            else:
                logger.warning("Session security system not available, skipping cleanup")
        except Exception as e:
            logger.error(f"Error during session cleanup: {str(e)}")
        
        time.sleep(interval_seconds)