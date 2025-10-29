"""
Health check and monitoring routes
"""
from fastapi import APIRouter, Request
import time
import logging
import psutil
import os
from datetime import datetime, timezone
from typing import Dict, Any
from app.utils.rate_limiter import limiter
from app.utils.logging_config import log_api_access

router = APIRouter(prefix='/health', tags=['health'])


@router.get(
    "/",
    summary="Comprehensive Health Check",
    description="Get detailed health status including system metrics, API metrics, and application status for production monitoring.",
    response_description="Returns comprehensive health status with system and application metrics",
    responses={
        200: {
            "description": "Health check completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-01-15T12:00:00Z",
                        "uptime_seconds": 3600.5,
                        "system": {
                            "cpu": {
                                "percent": 15.2,
                                "count": 8,
                                "status": "healthy"
                            },
                            "memory": {
                                "total_gb": 16.0,
                                "available_gb": 12.5,
                                "used_gb": 3.5,
                                "percent": 21.9,
                                "status": "healthy"
                            },
                            "disk": {
                                "total_gb": 500.0,
                                "free_gb": 400.0,
                                "used_gb": 100.0,
                                "percent": 20.0,
                                "status": "healthy"
                            }
                        },
                        "api": {
                            "active_sessions": 3,
                            "total_session_memory_mb": 5.8,
                            "status": "healthy"
                        },
                        "application": {
                            "uptime_seconds": 3600.5,
                            "python_version": "3.11.0",
                            "pid": 12345,
                            "status": "healthy"
                        },
                        "health_indicators": ["All systems operational"],
                        "processing_time_seconds": 0.089
                    }
                }
            }
        },
        500: {
            "description": "Health check failed",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "timestamp": "2024-01-15T12:00:00Z",
                        "error": "Failed to get system metrics",
                        "message": "Health check failed"
                    }
                }
            }
        }
    }
)
@limiter.limit("60/hour")
def health_check(request: Request):
    """
    Comprehensive health check endpoint for API monitoring
    
    Returns:
        dict: Health status with system metrics and API status
    """
    start_time = time.time()
    logger = logging.getLogger('data_summary_api')
    
    # Log API access
    client_ip = request.client.host if request.client else "unknown"
    log_api_access(logger, "/health", "GET", client_ip)
    
    try:
        # Get system metrics
        system_metrics = _get_system_metrics()
        
        # Get API metrics
        api_metrics = _get_api_metrics(request)
        
        # Get application metrics
        app_metrics = _get_application_metrics()
        
        # Calculate overall health status
        health_status = _calculate_health_status(system_metrics, api_metrics, app_metrics)
        
        processing_time = time.time() - start_time
        
        # Log health check
        logger.info(
            f"Health check completed",
            extra={'extra_data': {
                'event_type': 'health_check',
                'status': health_status['status'],
                'active_sessions': api_metrics['active_sessions'],
                'memory_usage_percent': system_metrics['memory']['percent'],
                'processing_time_seconds': round(processing_time, 3)
            }}
        )
        
        return {
            'status': health_status['status'],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'uptime_seconds': app_metrics['uptime_seconds'],
            'system': system_metrics,
            'api': api_metrics,
            'application': app_metrics,
            'health_indicators': health_status['indicators'],
            'processing_time_seconds': round(processing_time, 3)
        }
        
    except Exception as e:
        logger.error(
            f"Health check failed: {str(e)}",
            extra={'extra_data': {
                'event_type': 'health_check_error',
                'error_type': type(e).__name__,
                'error_message': str(e)
            }}
        )
        
        return {
            'status': 'unhealthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': str(e),
            'message': 'Health check failed'
        }


@router.get(
    "/simple",
    summary="Simple Health Check",
    description="Get basic health status for load balancer monitoring and quick status checks.",
    response_description="Returns basic health status",
    responses={
        200: {
            "description": "Health check completed",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-01-15T12:00:00Z",
                        "active_sessions": 3,
                        "memory_usage_percent": 21.9,
                        "disk_usage_percent": 20.0
                    }
                }
            }
        },
        500: {
            "description": "Health check failed",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "timestamp": "2024-01-15T12:00:00Z",
                        "error": "System metrics unavailable"
                    }
                }
            }
        }
    }
)
@limiter.limit("120/hour")
def simple_health_check(request: Request):
    """
    Simple health check for basic monitoring
    
    Returns:
        dict: Basic health status
    """
    logger = logging.getLogger('data_summary_api')
    
    try:
        # Basic checks
        session_security = request.app.state.session_security
        active_sessions = session_security.get_total_sessions()
        
        # Memory check
        memory = psutil.virtual_memory()
        memory_ok = memory.percent < 90
        
        # Disk space check
        disk = psutil.disk_usage('/')
        disk_ok = disk.percent < 90
        
        # Overall status
        status = 'healthy' if memory_ok and disk_ok else 'degraded'
        
        return {
            'status': status,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'active_sessions': active_sessions,
            'memory_usage_percent': round(memory.percent, 2),
            'disk_usage_percent': round(disk.percent, 2)
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': str(e)
        }


def _get_system_metrics() -> Dict[str, Any]:
    """Get system-level metrics"""
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        
        # Process metrics
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()
        
        return {
            'cpu': {
                'percent': round(cpu_percent, 2),
                'count': cpu_count,
                'status': 'healthy' if cpu_percent < 80 else 'warning' if cpu_percent < 95 else 'critical'
            },
            'memory': {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'percent': round(memory.percent, 2),
                'status': 'healthy' if memory.percent < 80 else 'warning' if memory.percent < 90 else 'critical'
            },
            'disk': {
                'total_gb': round(disk.total / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'percent': round(disk.percent, 2),
                'status': 'healthy' if disk.percent < 80 else 'warning' if disk.percent < 90 else 'critical'
            },
            'process': {
                'memory_mb': round(process_memory.rss / (1024**2), 2),
                'memory_percent': round(process_memory.rss / memory.total * 100, 2),
                'cpu_percent': round(process.cpu_percent(), 2)
            }
        }
    except Exception as e:
        return {
            'error': f"Failed to get system metrics: {str(e)}",
            'status': 'error'
        }


def _get_api_metrics(request: Request) -> Dict[str, Any]:
    """Get API-specific metrics"""
    try:
        session_security = request.app.state.session_security
        active_sessions = session_security.get_total_sessions()
        
        # Calculate total memory usage of all sessions
        total_session_memory = 0
        session_details = []
        
        for session_id, session_data in sessions.items():
            df = session_data.get('df')
            if df is not None:
                memory_usage = df.memory_usage(deep=True).sum()
                total_session_memory += memory_usage
                session_details.append({
                    'session_id': session_id,
                    'filename': session_data.get('filename', 'unknown'),
                    'row_count': session_data.get('row_count', 0),
                    'memory_mb': round(memory_usage / (1024**2), 2)
                })
        
        return {
            'active_sessions': active_sessions,
            'total_session_memory_mb': round(total_session_memory / (1024**2), 2),
            'session_details': session_details,
            'status': 'healthy' if active_sessions < 100 else 'warning' if active_sessions < 200 else 'critical'
        }
    except Exception as e:
        return {
            'error': f"Failed to get API metrics: {str(e)}",
            'status': 'error'
        }


def _get_application_metrics() -> Dict[str, Any]:
    """Get application-level metrics"""
    try:
        # Get process start time
        process = psutil.Process(os.getpid())
        start_time = process.create_time()
        uptime_seconds = time.time() - start_time
        
        # Get Python version and environment info
        import sys
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        return {
            'uptime_seconds': round(uptime_seconds, 2),
            'uptime_hours': round(uptime_seconds / 3600, 2),
            'python_version': python_version,
            'pid': os.getpid(),
            'status': 'healthy'
        }
    except Exception as e:
        return {
            'error': f"Failed to get application metrics: {str(e)}",
            'status': 'error'
        }


def _calculate_health_status(system_metrics: Dict[str, Any], api_metrics: Dict[str, Any], app_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate overall health status based on all metrics"""
    indicators = []
    status = 'healthy'
    
    # Check system metrics
    if 'error' not in system_metrics:
        if system_metrics['cpu']['status'] != 'healthy':
            indicators.append(f"High CPU usage: {system_metrics['cpu']['percent']}%")
            if system_metrics['cpu']['status'] == 'critical':
                status = 'unhealthy'
            elif status == 'healthy':
                status = 'degraded'
        
        if system_metrics['memory']['status'] != 'healthy':
            indicators.append(f"High memory usage: {system_metrics['memory']['percent']}%")
            if system_metrics['memory']['status'] == 'critical':
                status = 'unhealthy'
            elif status == 'healthy':
                status = 'degraded'
        
        if system_metrics['disk']['status'] != 'healthy':
            indicators.append(f"High disk usage: {system_metrics['disk']['percent']}%")
            if system_metrics['disk']['status'] == 'critical':
                status = 'unhealthy'
            elif status == 'healthy':
                status = 'degraded'
    
    # Check API metrics
    if 'error' not in api_metrics:
        if api_metrics['status'] != 'healthy':
            indicators.append(f"High session count: {api_metrics['active_sessions']}")
            if api_metrics['status'] == 'critical':
                status = 'unhealthy'
            elif status == 'healthy':
                status = 'degraded'
    
    # Check application metrics
    if 'error' in app_metrics:
        indicators.append("Application metrics unavailable")
        status = 'degraded'
    
    # If no issues found
    if not indicators:
        indicators.append("All systems operational")
    
    return {
        'status': status,
        'indicators': indicators
    }
