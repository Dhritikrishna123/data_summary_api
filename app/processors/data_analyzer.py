"""
Data analysis and processing utilities
"""
import pandas as pd
import numpy as np
from typing import Dict, Any


def get_memory_usage_estimate(df: pd.DataFrame) -> Dict[str, Any]:
    """Estimate memory usage of DataFrame"""
    memory_usage = df.memory_usage(deep=True)
    return {
        'total_bytes': int(memory_usage.sum()),
        'total_mb': round(memory_usage.sum() / (1024 * 1024), 2),
        'per_column': {col: int(memory_usage[col]) for col in df.columns}
    }


def get_data_types_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Get summary of data types for each column"""
    return {
        col: {
            'dtype': str(df[col].dtype),
            'category': df[col].dtype.kind,
            'non_null_count': int(df[col].count()),
            'null_count': int(df[col].isnull().sum()),
            'unique_count': int(df[col].nunique())
        }
        for col in df.columns
    }


def get_sample_data(df: pd.DataFrame, n_rows: int = 5) -> Dict[str, list]:
    """Get sample of first n rows"""
    sample_df = df.head(n_rows)
    # Convert to dict with proper JSON serialization
    sample_data = {}
    for col in sample_df.columns:
        sample_data[col] = sample_df[col].tolist()
    return sample_data


def compute_numeric_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute enhanced numeric summary statistics"""
    summary = {}
    numeric_cols = df.select_dtypes(include=np.number).columns
    
    for col in numeric_cols:
        try:
            series = pd.to_numeric(df[col], errors='coerce')
            summary[col] = {
                "mean": _safe_float(series.mean()),
                "median": _safe_float(series.median()),
                "std": _safe_float(series.std()),
                "min": _safe_float(series.min()),
                "max": _safe_float(series.max()),
                "count": int(series.count()),
                "missing": int(series.isna().sum()),
                "percent_missing": round((series.isna().sum() / len(series)) * 100, 2),
                "percentile_25": _safe_float(series.quantile(0.25)),
                "percentile_75": _safe_float(series.quantile(0.75))
            }
        except Exception:
            summary[col] = {
                "error": f"Could not compute summary for column {col}",
                "count": int(df[col].count()),
                "missing": int(df[col].isna().sum())
            }
    
    return summary


def compute_categorical_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute summary statistics for non-numeric columns"""
    summary = {}
    categorical_cols = df.select_dtypes(exclude=np.number).columns
    
    for col in categorical_cols:
        try:
            series = df[col]
            value_counts = series.value_counts()
            most_common = value_counts.index[0] if not value_counts.empty else None
            most_common_count = int(value_counts.iloc[0]) if not value_counts.empty else 0
            
            summary[col] = {
                "unique_count": int(series.nunique()),
                "most_common_value": most_common,
                "most_common_count": most_common_count,
                "count": int(series.count()),
                "missing": int(series.isna().sum()),
                "percent_missing": round((series.isna().sum() / len(series)) * 100, 2),
                "data_type": str(series.dtype)
            }
        except Exception:
            summary[col] = {
                "error": f"Could not compute summary for column {col}",
                "count": int(df[col].count()),
                "missing": int(df[col].isna().sum())
            }
    
    return summary


def compute_correlation_matrix(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute correlation matrix for numeric columns"""
    try:
        numeric_cols = df.select_dtypes(include=np.number).columns
        if len(numeric_cols) < 2:
            return {"message": "Need at least 2 numeric columns for correlation matrix"}
        
        corr_matrix = df[numeric_cols].corr()
        # Convert to dict for JSON serialization
        return {
            "columns": numeric_cols.tolist(),
            "correlation_matrix": corr_matrix.to_dict()
        }
    except Exception as e:
        return {"error": f"Could not compute correlation matrix: {str(e)}"}


def compute_data_quality_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute data quality metrics across all columns"""
    quality_metrics = {}
    
    for col in df.columns:
        series = df[col]
        missing_count = int(series.isna().sum())
        total_count = len(series)
        percent_missing = round((missing_count / total_count) * 100, 2)
        
        quality_metrics[col] = {
            "total_values": total_count,
            "missing_values": missing_count,
            "percent_missing": percent_missing,
            "data_quality": "excellent" if percent_missing < 5 else 
                          "good" if percent_missing < 20 else 
                          "fair" if percent_missing < 50 else "poor"
        }
    
    return quality_metrics


def _safe_float(x) -> float | None:
    """Convert x to float, return None if NaN or infinite."""
    try:
        if x is None or np.isnan(x) or np.isinf(x):
            return None
        return float(x)
    except:
        return None
