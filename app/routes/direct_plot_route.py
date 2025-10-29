from fastapi import APIRouter, HTTPException, Request, Body
import time
import logging
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.utils.rate_limiter import limiter
from app.utils.logging_config import log_api_access
from app.utils.custom_exceptions import PlotGenerationError, DataValidationError
from app.handlers.plot_generator import generate_plot, validate_plot_requirements

router = APIRouter(prefix="/direct-plot", tags=["direct-plot"])

class DirectPlotRequest(BaseModel):
    """Request model for direct plotting"""
    headers: List[str] = Field(..., description="Column headers", min_items=1, max_items=500)
    data: List[List[Any]] = Field(..., description="Data rows", min_items=1, max_items=1000000)
    plot_type: str = Field("histogram", description="Type of plot: histogram, boxplot, scatter, line")
    x_column: str = Field(..., description="X-axis column name")
    y_column: Optional[str] = Field(None, description="Y-axis column name (for scatter/line plots)")
    bins: int = Field(20, description="Number of bins for histogram", ge=5, le=100)
    color: str = Field("skyblue", description="Color for the plot")
    fig_width: int = Field(8, description="Figure width", ge=4, le=16)
    fig_height: int = Field(6, description="Figure height", ge=4, le=12)
    missing_strategy: str = Field("skip", description="How to handle missing values: skip, fill_mean, fill_median")

@router.post(
    "/",
    summary="Generate Plot from Direct Data Input",
    description="Create various types of plots directly from user-provided data without requiring file upload. Supports CSV-like data input with headers and rows.",
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
        400: {
            "description": "Invalid data or plot parameters",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid data format or missing required parameters"
                    }
                }
            }
        }
    }
)
@limiter.limit("30/hour")
def generate_direct_plot(
    request: Request,
    plot_request: DirectPlotRequest
):
    start_time = time.time()
    logger = logging.getLogger('data_summary_api')
    
    # Log API access
    client_ip = request.client.host if request.client else "unknown"
    log_api_access(logger, "/direct-plot", "POST", client_ip, "direct-input")
    
    try:
        # Validate data dimensions
        if len(plot_request.data) == 0:
            raise DataValidationError(
                detail="No data rows provided. Please provide at least one row of data.",
                context={'validation_type': 'empty_data', 'input_type': 'direct'}
            )
        
        # Check if all rows have the same number of columns as headers
        expected_cols = len(plot_request.headers)
        for i, row in enumerate(plot_request.data):
            if len(row) != expected_cols:
                raise DataValidationError(
                    detail=f"Row {i+1} has {len(row)} columns but expected {expected_cols} columns to match headers.",
                    context={'validation_type': 'column_mismatch', 'row_index': i, 'expected_cols': expected_cols, 'actual_cols': len(row)}
                )
        
        # Create DataFrame from the provided data
        df = pd.DataFrame(plot_request.data, columns=plot_request.headers)
        
        # Convert numeric columns to appropriate types
        for col in df.columns:
            # Try to convert to numeric, if it fails, keep as string
            df[col] = pd.to_numeric(df[col], errors='ignore')
        
        # Validate dataframe
        if df.empty:
            raise DataValidationError(
                detail="Created DataFrame is empty. Please check your data input.",
                context={'validation_type': 'empty_dataframe', 'input_type': 'direct'}
            )
        
        # Validate plot requirements
        validate_plot_requirements(df, plot_request.x_column)
        
        # Validate y_column for scatter/line plots
        if plot_request.plot_type in ['scatter', 'line'] and plot_request.y_column:
            if plot_request.y_column not in df.columns:
                raise DataValidationError(
                    detail=f"Y-axis column '{plot_request.y_column}' not found in data. Available columns: {', '.join(df.columns.tolist())}",
                    context={'validation_type': 'column_not_found', 'column_name': plot_request.y_column, 'available_columns': df.columns.tolist()}
                )
        
        # Generate plot using existing handler
        response = generate_plot(
            df=df,
            plot_type=plot_request.plot_type,
            x_column=plot_request.x_column,
            y_column=plot_request.y_column,
            bins=plot_request.bins,
            color=plot_request.color,
            figsize=(plot_request.fig_width, plot_request.fig_height),
            missing_strategy=plot_request.missing_strategy
        )
        
        processing_time = time.time() - start_time
        non_null_count = df[plot_request.x_column].count()
        
        # Log successful plot generation
        logger.info(
            f"Direct plot generated for column {plot_request.x_column}",
            extra={'extra_data': {
                'event_type': 'direct_plot_success',
                'column_name': plot_request.x_column,
                'plot_type': plot_request.plot_type,
                'data_points': int(non_null_count),
                'missing_values': int(df[plot_request.x_column].isnull().sum()),
                'processing_time_seconds': round(processing_time, 3),
                'input_type': 'direct'
            }}
        )

        return response
            
    except (DataValidationError, PlotGenerationError) as e:
        # These are expected errors, just re-raise
        raise e
        
    except Exception as e:
        # Log unexpected errors
        logger.error(
            f"Unexpected error in direct plot generation: {str(e)}",
            extra={'extra_data': {
                'event_type': 'direct_plot_error',
                'column_name': plot_request.x_column,
                'plot_type': plot_request.plot_type,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'input_type': 'direct'
            }}
        )
        raise PlotGenerationError(
            detail="An unexpected error occurred while generating the plot. Please check your data format and try again.",
            column_name=plot_request.x_column,
            context={'plot_type': plot_request.plot_type, 'original_error': str(e), 'input_type': 'direct'}
        )
