from fastapi import HTTPException
import magic

MAX_FILE_SIZE = 30

def validate_file_size(file_bytes: bytes, max_file_size: int = MAX_FILE_SIZE):
    size_mb = len(file_bytes) / 1024 / 1024
    if size_mb > max_file_size:
        raise HTTPException(status_code=400, detail=f"File size {size_mb:.2f}MB exceeds limit of {max_file_size}MB.")


def validate_file_type(file_bytes: bytes):
    try:
        mime_type = magic.from_buffer(file_bytes, mime=True)
        file_type = magic.from_buffer(file_bytes)

        # log the detection result for debugging
        print(f"Magic detection - MIME: {mime_type}, Type: {file_type}")

        allowed_types = [
            "text/csv",
            "application/csv",
            "text/plain",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ]

        if mime_type not in allowed_types:
            # Additional validation for CSV files that might not be detected properly
            is_csv = is_likely_csv(file_bytes)
            print(f"Magic failed, CSV content check: {is_csv}")

            if is_csv:
                return  # Allow CSV files that look like CSV even if magic detection fails
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type '{mime_type}' is not supported. Only CSV and XLSX files are allowed."
                )
    except Exception as e:
        print(f"Magic detection failed: {e}")
        # If magic detection fails, try to validate based on content
        is_csv = is_likely_csv(file_bytes)
        print(f"Magic exception, CSV content check: {is_csv}")

        if is_csv:
            return  # Allow CSV files based on content analysis
        else:
            raise HTTPException(
                status_code=400,
                detail=f"File type detection failed. Only CSV and XLSX files are allowed."
            )


def is_likely_csv(file_bytes: bytes) -> bool:
    """
    Check if the file content looks like a CSV file
    """
    try:
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        content = None

        for encoding in encodings:
            try:
                content = file_bytes[:2048].decode(encoding, errors='ignore')
                break
            except:
                continue

        if not content:
            return False

        print(f"CSV content check - First 200 chars: {content[:200]}")

        # Check for CSV patterns
        lines = content.split('\n')
        if len(lines) < 2:
            print("CSV check failed: Less than 2 lines")
            return False

        # Check if first line contains commas (likely headers)
        first_line = lines[0].strip()
        if ',' not in first_line:
            print("CSV check failed: No commas in first line")
            return False

        # Check if we have at least one data row with similar structure
        data_lines = [line.strip() for line in lines[1:] if line.strip()]
        if not data_lines:
            print("CSV check failed: No data lines")
            return False

        # Check if data rows have similar column count to headers
        header_columns = first_line.count(',') + 1
        print(f"CSV check - Header columns: {header_columns}")

        valid_rows = 0
        for i, line in enumerate(data_lines[:10]):  # Check first 10 data lines
            line_columns = line.count(',') + 1
            print(f"CSV check - Row {i + 1} columns: {line_columns}")
            if abs(line_columns - header_columns) <= 2:  # Allow for more variations
                valid_rows += 1

        print(f"CSV check - Valid rows: {valid_rows}")
        return valid_rows > 0

    except Exception as e:
        print(f"CSV check exception: {e}")
        return False