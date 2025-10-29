"""
Large file processing handlers for better memory management
"""
import pandas as pd
import io
from typing import Optional, Dict, Any, Iterator
from app.utils.custom_exceptions import FileReadError, DataFrameValidationError


def parse_large_file(
    filename: str, 
    contents: bytes, 
    chunk_size: int = 10000,
    sample_rows: Optional[int] = None,
    encoding: str = None
) -> tuple[pd.DataFrame, str, Dict[str, Any]]:
    """
    Parse large files with chunked reading and optional sampling
    
    Args:
        filename: Name of the uploaded file
        contents: File contents as bytes
        chunk_size: Number of rows to read per chunk
        sample_rows: If provided, only read first N rows
        encoding: Optional encoding to use
        
    Returns:
        tuple: (DataFrame, filetype, metadata)
        
    Raises:
        FileReadError: If file parsing fails
        DataFrameValidationError: If DataFrame validation fails
    """
    metadata = {
        'chunk_size': chunk_size,
        'sample_rows': sample_rows,
        'is_sampled': sample_rows is not None
    }
    
    if filename.lower().endswith('.csv'):
        try:
            df, filetype, file_metadata = _parse_large_csv(
                contents, chunk_size, sample_rows, encoding
            )
            metadata.update(file_metadata)
            return df, filetype, metadata
        except Exception as e:
            raise FileReadError(filename, 'CSV', str(e))
    else:
        # For Excel files, use regular parsing (Excel files are typically smaller)
        try:
            df = pd.read_excel(io.BytesIO(contents))
            filetype = 'XLSX'
            metadata['total_rows'] = len(df)
            return df, filetype, metadata
        except Exception as e:
            raise FileReadError(filename, 'XLSX', str(e))


def _parse_large_csv(
    contents: bytes, 
    chunk_size: int, 
    sample_rows: Optional[int], 
    encoding: str = None
) -> tuple[pd.DataFrame, str, Dict[str, Any]]:
    """
    Parse large CSV with chunked reading
    """
    from app.handlers.file_parser import _parse_csv_with_encoding, detect_file_encoding
    
    # Detect encoding if not provided
    if not encoding:
        encoding_info = detect_file_encoding(contents)
        encoding = encoding_info.get('encoding', 'utf-8')
    
    # If sampling is requested, read only first N rows
    if sample_rows:
        try:
            df = pd.read_csv(
                io.BytesIO(contents), 
                encoding=encoding, 
                nrows=sample_rows
            )
            return df, 'CSV', {
                'encoding': encoding,
                'total_rows': len(df),
                'is_sampled': True,
                'sample_size': sample_rows
            }
        except Exception as e:
            raise FileReadError("CSV", "CSV", f"Failed to sample CSV: {str(e)}")
    
    # For full file processing, use chunked reading
    try:
        # First, get the total number of rows
        total_rows = _count_csv_rows(contents, encoding)
        
        # If file is small enough, read it normally
        if total_rows <= chunk_size:
            df, detected_encoding = _parse_csv_with_encoding(contents, encoding)
            return df, 'CSV', {
                'encoding': detected_encoding,
                'total_rows': total_rows,
                'is_chunked': False
            }
        
        # For large files, read in chunks
        df = _read_csv_in_chunks(contents, chunk_size, encoding)
        
        return df, 'CSV', {
            'encoding': encoding,
            'total_rows': total_rows,
            'is_chunked': True,
            'chunk_size': chunk_size
        }
        
    except Exception as e:
        raise FileReadError("CSV", "CSV", f"Failed to parse large CSV: {str(e)}")


def _count_csv_rows(contents: bytes, encoding: str) -> int:
    """Count total rows in CSV file"""
    try:
        # Read just the first few bytes to get column headers
        sample_size = min(1024, len(contents))
        sample = contents[:sample_size].decode(encoding, errors='ignore')
        lines = sample.count('\n')
        
        # Estimate total rows based on file size
        if lines > 0:
            estimated_rows = (len(contents) / len(contents[:sample_size])) * lines
            return int(estimated_rows)
        else:
            return 0
    except Exception:
        return 0


def _read_csv_in_chunks(contents: bytes, chunk_size: int, encoding: str) -> pd.DataFrame:
    """Read CSV in chunks and combine"""
    try:
        # Create a list to store chunks
        chunks = []
        
        # Read the file in chunks
        for chunk in pd.read_csv(io.BytesIO(contents), encoding=encoding, chunksize=chunk_size):
            chunks.append(chunk)
            
            # Limit to reasonable number of chunks to prevent memory issues
            if len(chunks) > 100:  # Max 1M rows (100 * 10k)
                break
        
        # Combine all chunks
        if chunks:
            df = pd.concat(chunks, ignore_index=True)
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        raise FileReadError("CSV", "CSV", f"Failed to read CSV in chunks: {str(e)}")


def get_file_preview(
    contents: bytes, 
    filename: str, 
    preview_rows: int = 5,
    encoding: str = None
) -> Dict[str, Any]:
    """
    Get a preview of the file without loading the entire dataset
    
    Args:
        contents: File contents as bytes
        filename: Name of the file
        preview_rows: Number of rows to preview
        encoding: Optional encoding to use
        
    Returns:
        dict: Preview information
    """
    try:
        if filename.lower().endswith('.csv'):
            # Get encoding info
            from app.handlers.file_parser import detect_file_encoding
            encoding_info = detect_file_encoding(contents)
            
            # Read preview
            df_preview = pd.read_csv(
                io.BytesIO(contents), 
                encoding=encoding or encoding_info.get('encoding', 'utf-8'),
                nrows=preview_rows
            )
            
            return {
                'preview_data': df_preview.to_dict('records'),
                'columns': df_preview.columns.tolist(),
                'preview_rows': len(df_preview),
                'encoding': encoding_info.get('encoding', 'utf-8'),
                'encoding_confidence': encoding_info.get('confidence', 0),
                'file_type': 'CSV'
            }
        else:
            # For Excel files
            df_preview = pd.read_excel(io.BytesIO(contents), nrows=preview_rows)
            
            return {
                'preview_data': df_preview.to_dict('records'),
                'columns': df_preview.columns.tolist(),
                'preview_rows': len(df_preview),
                'file_type': 'XLSX'
            }
            
    except Exception as e:
        return {
            'error': f"Failed to preview file: {str(e)}",
            'file_type': 'CSV' if filename.lower().endswith('.csv') else 'XLSX'
        }
