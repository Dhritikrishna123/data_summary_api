"""
Missing value handling and analysis
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from app.utils.custom_exceptions import DataValidationError


def get_missing_value_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate comprehensive missing value report
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        dict: Missing value report
    """
    report = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'columns_with_missing': [],
        'missing_summary': {},
        'missing_patterns': {},
        'recommendations': []
    }
    
    # Analyze each column
    for col in df.columns:
        missing_count = int(df[col].isna().sum())
        missing_percent = round((missing_count / len(df)) * 100, 2)
        
        col_report = {
            'missing_count': missing_count,
            'missing_percent': missing_percent,
            'non_missing_count': int(df[col].count()),
            'data_type': str(df[col].dtype),
            'quality_rating': _get_quality_rating(missing_percent)
        }
        
        report['missing_summary'][col] = col_report
        
        if missing_count > 0:
            report['columns_with_missing'].append(col)
            
            # Analyze missing patterns
            if missing_percent > 50:
                report['missing_patterns'][col] = 'high_missing'
            elif missing_percent > 20:
                report['missing_patterns'][col] = 'moderate_missing'
            else:
                report['missing_patterns'][col] = 'low_missing'
    
    # Generate recommendations
    report['recommendations'] = _generate_missing_value_recommendations(report)
    
    return report


def _get_quality_rating(missing_percent: float) -> str:
    """Get data quality rating based on missing percentage"""
    if missing_percent < 5:
        return 'excellent'
    elif missing_percent < 20:
        return 'good'
    elif missing_percent < 50:
        return 'fair'
    else:
        return 'poor'


def _generate_missing_value_recommendations(report: Dict[str, Any]) -> List[str]:
    """Generate recommendations for handling missing values"""
    recommendations = []
    
    high_missing_cols = [
        col for col, pattern in report['missing_patterns'].items() 
        if pattern == 'high_missing'
    ]
    
    moderate_missing_cols = [
        col for col, pattern in report['missing_patterns'].items() 
        if pattern == 'moderate_missing'
    ]
    
    if high_missing_cols:
        recommendations.append(
            f"Consider dropping columns with >50% missing values: {', '.join(high_missing_cols)}"
        )
    
    if moderate_missing_cols:
        recommendations.append(
            f"Consider imputation strategies for columns with 20-50% missing values: {', '.join(moderate_missing_cols)}"
        )
    
    if not report['columns_with_missing']:
        recommendations.append("No missing values detected - data quality is excellent!")
    
    return recommendations


def handle_missing_values(
    df: pd.DataFrame, 
    strategy: str = 'skip',
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Handle missing values based on specified strategy
    
    Args:
        df: DataFrame to process
        strategy: Strategy to use ('skip', 'fill_mean', 'fill_median', 'fill_mode', 'forward_fill', 'backward_fill')
        columns: Specific columns to process (if None, processes all columns)
        
    Returns:
        pd.DataFrame: Processed DataFrame
    """
    df_processed = df.copy()
    
    if columns is None:
        columns = df.columns.tolist()
    
    for col in columns:
        if col not in df.columns:
            continue
            
        if strategy == 'skip':
            # Drop rows with missing values in specified columns
            df_processed = df_processed.dropna(subset=[col])
            
        elif strategy == 'fill_mean':
            # Fill with mean (numeric columns only)
            if df_processed[col].dtype in ['int64', 'float64']:
                df_processed[col] = df_processed[col].fillna(df_processed[col].mean())
            else:
                # For non-numeric, use mode
                mode_value = df_processed[col].mode()
                if not mode_value.empty:
                    df_processed[col] = df_processed[col].fillna(mode_value[0])
                    
        elif strategy == 'fill_median':
            # Fill with median (numeric columns only)
            if df_processed[col].dtype in ['int64', 'float64']:
                df_processed[col] = df_processed[col].fillna(df_processed[col].median())
            else:
                # For non-numeric, use mode
                mode_value = df_processed[col].mode()
                if not mode_value.empty:
                    df_processed[col] = df_processed[col].fillna(mode_value[0])
                    
        elif strategy == 'fill_mode':
            # Fill with most common value
            mode_value = df_processed[col].mode()
            if not mode_value.empty:
                df_processed[col] = df_processed[col].fillna(mode_value[0])
                
        elif strategy == 'forward_fill':
            # Forward fill
            df_processed[col] = df_processed[col].fillna(method='ffill')
            
        elif strategy == 'backward_fill':
            # Backward fill
            df_processed[col] = df_processed[col].fillna(method='bfill')
    
    return df_processed


def get_missing_value_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get detailed missing value statistics
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        dict: Detailed missing value statistics
    """
    stats = {
        'overall': {
            'total_cells': len(df) * len(df.columns),
            'missing_cells': int(df.isna().sum().sum()),
            'missing_percentage': round((df.isna().sum().sum() / (len(df) * len(df.columns))) * 100, 2)
        },
        'by_column': {},
        'by_row': {
            'rows_with_missing': int(df.isna().any(axis=1).sum()),
            'rows_without_missing': int((~df.isna().any(axis=1)).sum()),
            'rows_all_missing': int(df.isna().all(axis=1).sum())
        }
    }
    
    # Column-wise statistics
    for col in df.columns:
        missing_count = int(df[col].isna().sum())
        stats['by_column'][col] = {
            'missing_count': missing_count,
            'missing_percentage': round((missing_count / len(df)) * 100, 2),
            'non_missing_count': int(df[col].count())
        }
    
    return stats
