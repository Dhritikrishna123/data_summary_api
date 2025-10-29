"""
Plot generation handlers
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import io
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
from app.utils.custom_exceptions import PlotGenerationError


def generate_plot(
    df: pd.DataFrame, 
    plot_type: str = 'histogram',
    x_column: Optional[str] = None,
    y_column: Optional[str] = None,
    bins: int = 20,
    color: str = 'skyblue',
    figsize: tuple = (8, 6),
    missing_strategy: str = 'skip'
) -> StreamingResponse:
    """
    Generate various types of plots
    
    Args:
        df: DataFrame containing the data
        plot_type: Type of plot ('histogram', 'boxplot', 'scatter', 'line')
        x_column: X-axis column name
        y_column: Y-axis column name (for scatter/line plots)
        bins: Number of bins for histogram
        color: Color for the plot
        figsize: Figure size tuple
        missing_strategy: How to handle missing values ('skip', 'fill_mean', 'fill_median')
        
    Returns:
        StreamingResponse: PNG image of the plot
        
    Raises:
        PlotGenerationError: If plot generation fails
    """
    try:
        plt.figure(figsize=figsize)
        
        if plot_type == 'histogram':
            return _generate_histogram(df, x_column, bins, color, missing_strategy)
        elif plot_type == 'boxplot':
            return _generate_boxplot(df, x_column, color, missing_strategy)
        elif plot_type == 'scatter':
            return _generate_scatter(df, x_column, y_column, color, missing_strategy)
        elif plot_type == 'line':
            return _generate_line(df, x_column, y_column, color, missing_strategy)
        else:
            raise PlotGenerationError(
                detail=f"Unsupported plot type: {plot_type}. Supported types: histogram, boxplot, scatter, line",
                column_name=x_column,
                context={'plot_type': plot_type}
            )
            
    except Exception as e:
        raise PlotGenerationError(
            detail=f"Failed to generate {plot_type} plot: {str(e)}",
            column_name=x_column,
            context={'original_error': str(e), 'plot_type': plot_type}
        )


def _generate_histogram(df: pd.DataFrame, column: str, bins: int, color: str, missing_strategy: str) -> StreamingResponse:
    """Generate histogram plot"""
    data = _handle_missing_values(df[column], missing_strategy)
    
    # Use matplotlib's hist function directly, not pandas' hist method
    n, bins_edges, patches = plt.hist(data, bins=bins, color=color, edgecolor="black", alpha=0.7)
    
    mean_val = data.mean()
    std_val = data.std()
    
    plt.title(f"Histogram of {column}\n(Mean: {mean_val:.2f}, Std: {std_val:.2f})", fontsize=12)
    plt.xlabel(column, fontsize=10)
    plt.ylabel("Frequency", fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    return _create_streaming_response()


def _generate_boxplot(df: pd.DataFrame, column: str, color: str, missing_strategy: str) -> StreamingResponse:
    """Generate boxplot"""
    data = _handle_missing_values(df[column], missing_strategy)
    
    box_plot = plt.boxplot(data, patch_artist=True)
    box_plot['boxes'][0].set_facecolor(color)
    
    plt.title(f"Boxplot of {column}", fontsize=12)
    plt.ylabel(column, fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    return _create_streaming_response()


def _generate_scatter(df: pd.DataFrame, x_column: str, y_column: str, color: str, missing_strategy: str) -> StreamingResponse:
    """Generate scatter plot"""
    x_data = _handle_missing_values(df[x_column], missing_strategy)
    y_data = _handle_missing_values(df[y_column], missing_strategy)
    
    plt.scatter(x_data, y_data, color=color, alpha=0.6)
    
    plt.title(f"Scatter Plot: {x_column} vs {y_column}", fontsize=12)
    plt.xlabel(x_column, fontsize=10)
    plt.ylabel(y_column, fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    return _create_streaming_response()


def _generate_line(df: pd.DataFrame, x_column: str, y_column: str, color: str, missing_strategy: str) -> StreamingResponse:
    """Generate line plot"""
    x_data = _handle_missing_values(df[x_column], missing_strategy)
    y_data = _handle_missing_values(df[y_column], missing_strategy)
    
    plt.plot(x_data, y_data, color=color, linewidth=2)
    
    plt.title(f"Line Plot: {x_column} vs {y_column}", fontsize=12)
    plt.xlabel(x_column, fontsize=10)
    plt.ylabel(y_column, fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    return _create_streaming_response()


def _handle_missing_values(series: pd.Series, strategy: str) -> pd.Series:
    """Handle missing values based on strategy"""
    if strategy == 'skip':
        return series.dropna()
    elif strategy == 'fill_mean':
        return series.fillna(series.mean())
    elif strategy == 'fill_median':
        return series.fillna(series.median())
    else:
        return series


def _create_streaming_response() -> StreamingResponse:
    """Create streaming response from current plot"""
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return StreamingResponse(buf, media_type='image/png')


def generate_histogram(df: pd.DataFrame, column: str) -> StreamingResponse:
    """
    Generate histogram for a numeric column (legacy function for backward compatibility)
    
    Args:
        df: DataFrame containing the data
        column: Column name to plot
        
    Returns:
        StreamingResponse: PNG image of the histogram
        
    Raises:
        PlotGenerationError: If plot generation fails
    """
    return generate_plot(df, plot_type='histogram', x_column=column)


def validate_plot_requirements(df: pd.DataFrame, column: str) -> None:
    """
    Validate requirements for plotting a column
    
    Args:
        df: DataFrame containing the data
        column: Column name to validate
        
    Raises:
        ColumnValidationError: If column validation fails
    """
    from app.utils.custom_exceptions import ColumnValidationError
    
    if column not in df.columns:
        available_columns = df.columns.tolist()
        raise ColumnValidationError(
            detail=f"Column '{column}' not found in dataset. Available columns: {', '.join(available_columns)}",
            column_name=column,
            issue_type='column_not_found'
        )

    # Check if column is numeric
    if df[column].dtype.kind not in 'biufc':  # integer, boolean, unsigned, float, complex
        raise ColumnValidationError(
            detail=f"Column '{column}' is not numeric (type: {df[column].dtype}) and cannot be plotted. Only numeric columns can be visualized with histograms.",
            column_name=column,
            column_type=str(df[column].dtype),
            issue_type='non_numeric_column'
        )
    
    # Check if column has any non-null values
    non_null_count = df[column].count()
    if non_null_count == 0:
        raise ColumnValidationError(
            detail=f"Column '{column}' contains no valid data (all values are null). Cannot generate plot.",
            column_name=column,
            issue_type='empty_column'
        )