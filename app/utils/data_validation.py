from fastapi import HTTPException
import pandas as pd

def validate_dataframe(df: pd.DataFrame, min_rows = 1, max_rows = 1000000, min_cols = 1, max_cols = 500):
    if df is None or df.empty:
        raise HTTPException(status_code=400,detail="Uploaded file is empty.")
    
    
    rows, cols = df.shape
    if rows < min_rows or cols < min_cols:
        raise HTTPException(status_code=400, detail=f"File must have at least {min_rows} row and {min_cols} column.")
    if rows > max_rows:
        raise HTTPException(status_code=400, detail=f"File exceeds maximum allowed rows ({max_rows}).")
    if cols > max_cols:
        raise HTTPException(status_code=400, detail=f"File exceeds maximum allowed columns ({max_cols}).")

    if any(str(c).startswith("unnamed") for c in df.columns):
        raise HTTPException(status_code=400, detail="File Appears to have missing or invalid headers.")