from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.upload_route import router as upload_router
from app.routes.summary_route import router as summary_route
from app.routes.plot_route import router as plot_router
from app.routes.direct_plot_route import router as direct_plot_router
from app.routes.session_route import router as session_router
from app.routes.column_route import router as column_router
from app.routes.missing_values_route import router as missing_values_router
from app.routes.export_route import router as export_router
from app.routes.health_route import router as health_router
from app.utils.session_manager import cleanup_expired_sessions
from app.utils.session_security import session_security
from app.utils.rate_limiter import limiter
from app.utils.logging_config import setup_logging
from slowapi.middleware import SlowAPIMiddleware
from datetime import timezone
import threading
import time

app = FastAPI(
    title="Data Summary API",
    description="""
    A comprehensive data analysis API that provides statistical summaries, visualizations, and data management capabilities for uploaded datasets.
    
    ## Features
    
    * **File Upload**: Support for CSV and Excel files with automatic encoding detection
    * **Statistical Analysis**: Comprehensive summary statistics including numeric and categorical analysis
    * **Data Visualization**: Multiple plot types (histogram, boxplot, scatter, line) with customization options
    * **Session Management**: Track and manage multiple data analysis sessions
    * **Missing Value Handling**: Advanced missing value analysis and imputation strategies
    * **Data Export**: Export processed data in CSV or JSON formats
    * **Health Monitoring**: Comprehensive health checks for production monitoring
    
    ## Rate Limiting
    
    The API implements rate limiting to ensure fair usage:
    - Upload endpoints: 20 requests/hour
    - Summary endpoints: 20 requests/hour  
    - Plot endpoints: 30 requests/hour
    - Session endpoints: 30 requests/hour
    - Health endpoints: 60 requests/hour (simple: 120 requests/hour)
    
    ## File Constraints
    
    - **Maximum file size**: 100MB
    - **Supported formats**: CSV, XLSX
    - **Minimum rows**: 1
    - **Maximum rows**: 1,000,000
    - **Minimum columns**: 1
    - **Maximum columns**: 500
    
    ## Session Management
    
    - Sessions expire after 1 hour of inactivity
    - Maximum 200 sessions per instance
    - Automatic cleanup every 10 minutes
    """,
    version="1.0.0",
    contact={
        "name": "Data Summary API Support",
        "email": "support@datasummaryapi.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.datasummary.com",
            "description": "Production server"
        }
    ]
)

# Setup logging
logger = setup_logging()

# Add CORS middleware
import os
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Set via environment variable for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#---session storage ---
# Use secure session system instead of shared dictionary
app.state.session_security = session_security

# start cleanup thread
threading.Thread(
    target=cleanup_expired_sessions,
    args=(app,),
    daemon=True,
).start()

# slowapi middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# routers
app.include_router(upload_router)
app.include_router(summary_route)
app.include_router(plot_router)
app.include_router(direct_plot_router)
app.include_router(session_router)
app.include_router(column_router)
app.include_router(missing_values_router)
app.include_router(export_router)
app.include_router(health_router)


@app.get("/")
def root():
    return {'message': 'Data Summary Api is running ... '}

@app.get("/cors-test")
def cors_test():
    return {'message': 'CORS is working!', 'status': 'success'}