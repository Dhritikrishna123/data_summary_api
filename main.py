from fastapi import FastAPI

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

@app.get("/")
def root():
    return {'message': 'Data Summary Api is running ... '}