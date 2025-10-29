from fastapi import APIRouter, HTTPException, Request, Query
import time
import logging
from datetime import datetime, timezone
from app.utils.rate_limiter import limiter
from app.utils.logging_config import log_api_access
from app.utils.custom_exceptions import SessionNotFoundError, ColumnValidationError, PlotGenerationError, DataValidationError
from app.handlers.plot_generator import generate_plot, validate_plot_requirements

router = APIRouter(prefix="/plot", tags=["plot"])

@router.get(
    "/",
    summary="Generate Data Visualization",
    description="Create various types of plots for data visualization including histograms, boxplots, scatter plots, and line plots with customizable parameters.",
    response_description="Returns a PNG image of the generated plot",
    responses={
        200: {
            "description": "Plot generated successfully",
            "content": {
                "image/png": {
                    "schema": {
                        "type": "string",
                        "format": "binary"
                    }
                }
            }
        },
        404: {
            "description": "Session not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Session 'invalid-session-id' not found"
                    }
                }
            }
        },
        400: {
            "description": "Invalid column or plot parameters",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Column 'invalid_column' not found in dataset. Available columns: age, salary, department"
                    }
                }
            }
        }
    }
)
@limiter.limit("30/hour")
def plot_column(
    request: Request,
    session_id: str = Query(..., description="Unique session ID for uploaded file"),
    column: str = Query(..., description="Column to plot"),
    plot_type: str = Query("histogram", description="Type of plot: histogram, boxplot, scatter, line"),
    y_column: str = Query(None, description="Y-axis column for scatter/line plots"),
    bins: int = Query(20, description="Number of bins for histogram"),
    color: str = Query("skyblue", description="Color for the plot"),
    fig_width: int = Query(8, description="Figure width"),
    fig_height: int = Query(6, description="Figure height"),
    missing_strategy: str = Query("skip", description="How to handle missing values: skip, fill_mean, fill_median")
):
    start_time = time.time()
    logger = logging.getLogger('data_summary_api')
    
    # Log API access
    client_ip = request.client.host if request.client else "unknown"
    log_api_access(logger, "/plot", "GET", client_ip, session_id)
    
    try:
        # --- Retrieve session ---
        session_security = request.app.state.session_security
        session = session_security.get_session(session_id, client_ip)
        if not session:
            raise SessionNotFoundError(session_id)

        df = session.get("df")

        # --- Validate dataframe and column ---
        if df is None or df.empty:
            raise DataValidationError(
                detail="Uploaded file is empty or invalid. Please upload a valid file with data.",
                context={'validation_type': 'empty_dataframe', 'session_id': session_id}
            )

        # Validate plot requirements using modular handler
        validate_plot_requirements(df, column)
        
        # Validate y_column for scatter/line plots
        if plot_type in ['scatter', 'line'] and y_column:
            if y_column not in df.columns:
                raise ColumnValidationError(
                    detail=f"Y-axis column '{y_column}' not found in dataset. Available columns: {', '.join(df.columns.tolist())}",
                    column_name=y_column,
                    issue_type='column_not_found'
                )

        # Generate plot using enhanced handler
        response = generate_plot(
            df=df,
            plot_type=plot_type,
            x_column=column,
            y_column=y_column,
            bins=bins,
            color=color,
            figsize=(fig_width, fig_height),
            missing_strategy=missing_strategy
        )
        
        processing_time = time.time() - start_time
        non_null_count = df[column].count()
        
        # Log successful plot generation
        logger.info(
            f"Plot generated for column {column} in session {session_id}",
            extra={'extra_data': {
                'event_type': 'plot_success',
                'session_id': session_id,
                'column_name': column,
                'data_points': int(non_null_count),
                'missing_values': int(df[column].isnull().sum()),
                'processing_time_seconds': round(processing_time, 3)
            }}
        )

        return response
            
    except (SessionNotFoundError, ColumnValidationError, DataValidationError, PlotGenerationError) as e:
        # These are expected errors, just re-raise
        raise e
        
    except Exception as e:
        # Log unexpected errors
        logger.error(
            f"Unexpected error in plot generation: {str(e)}",
            extra={'extra_data': {
                'event_type': 'plot_error',
                'session_id': session_id,
                'column_name': column,
                'error_type': type(e).__name__,
                'error_message': str(e)
            }}
        )
        raise PlotGenerationError(
            detail="An unexpected error occurred while generating the plot. Please try again.",
            column_name=column,
            context={'session_id': session_id, 'original_error': str(e)}
        )
