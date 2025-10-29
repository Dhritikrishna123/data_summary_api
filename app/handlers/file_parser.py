"""
File parsing handlers for different file formats
"""
import pandas as pd
import io
import chardet
from app.utils.custom_exceptions import FileReadError, DataFrameValidationError
from app.utils.data_validation import validate_dataframe


def parse_file_contents(filename: str, contents: bytes, encoding: str = None) -> tuple[pd.DataFrame, str]:
    """
    Parse file contents based on file extension with encoding detection
    
    Args:
        filename: Name of the uploaded file
        contents: File contents as bytes
        encoding: Optional encoding to use (if None, will auto-detect)
        
    Returns:
        tuple: (DataFrame, filetype)
        
    Raises:
        FileReadError: If file parsing fails
        DataFrameValidationError: If DataFrame validation fails
    """
    # Determine file type and parse accordingly
    if filename.lower().endswith('.csv'):
        try:
            df, detected_encoding = _parse_csv_with_encoding(contents, encoding)
            filetype = 'CSV'
        except Exception as e:
            raise FileReadError(filename, 'CSV', str(e))
    else:
        try:
            df = pd.read_excel(io.BytesIO(contents))
            filetype = 'XLSX'
        except Exception as e:
            raise FileReadError(filename, 'XLSX', str(e))
    
    # Validate DataFrame structure
    try:
        validate_dataframe(df)
    except Exception as e:
        row_count, col_count = df.shape if df is not None and not df.empty else (0, 0)
        raise DataFrameValidationError(
            detail=str(e.detail) if hasattr(e, 'detail') else str(e),
            row_count=row_count,
            col_count=col_count,
            min_rows=1,
            max_rows=1000000,
            min_cols=1,
            max_cols=500
        )
    
    return df, filetype


def _parse_csv_with_encoding(contents: bytes, encoding: str = None) -> tuple[pd.DataFrame, str]:
    """
    Parse CSV with automatic encoding detection
    
    Args:
        contents: File contents as bytes
        encoding: Optional encoding to use
        
    Returns:
        tuple: (DataFrame, detected_encoding)
        
    Raises:
        FileReadError: If parsing fails with all encodings
    """
    # Common encodings to try
    common_encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
    
    if encoding:
        # Use specified encoding
        try:
            df = pd.read_csv(io.BytesIO(contents), encoding=encoding)
            return df, encoding
        except Exception as e:
            raise FileReadError("CSV", "CSV", f"Failed to parse with specified encoding '{encoding}': {str(e)}")
    
    # Try to detect encoding
    try:
        detected = chardet.detect(contents)
        detected_encoding = detected.get('encoding', 'utf-8')
        confidence = detected.get('confidence', 0)
        
        # If confidence is high, try the detected encoding first
        if confidence > 0.7:
            try:
                df = pd.read_csv(io.BytesIO(contents), encoding=detected_encoding)
                return df, detected_encoding
            except Exception:
                pass  # Fall back to common encodings
    except Exception:
        pass  # Fall back to common encodings
    
    # Try common encodings in order
    for enc in common_encodings:
        try:
            df = pd.read_csv(io.BytesIO(contents), encoding=enc)
            return df, enc
        except Exception:
            continue
    
    # If all encodings fail, try with error handling
    try:
        df = pd.read_csv(io.BytesIO(contents), encoding='utf-8', errors='replace')
        return df, 'utf-8'
    except Exception as e:
        raise FileReadError("CSV", "CSV", f"Failed to parse CSV with any encoding. Last error: {str(e)}")


def detect_file_encoding(contents: bytes) -> dict:
    """
    Detect file encoding
    
    Args:
        contents: File contents as bytes
        
    Returns:
        dict: Encoding detection results
    """
    try:
        result = chardet.detect(contents)
        return {
            'encoding': result.get('encoding', 'unknown'),
            'confidence': result.get('confidence', 0),
            'language': result.get('language', 'unknown')
        }
    except Exception as e:
        return {
            'encoding': 'unknown',
            'confidence': 0,
            'language': 'unknown',
            'error': str(e)
        }
