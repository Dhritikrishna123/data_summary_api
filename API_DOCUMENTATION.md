# Data Summary API - Complete Documentation

## Overview

The Data Summary API is a comprehensive data analysis service that provides statistical summaries, visualizations, and data management capabilities for uploaded datasets. The API supports CSV and Excel files with advanced features for data exploration and analysis.

## Base URL

```[bash]
http://localhost:8000
```

## Authentication

No authentication required for this API.

## Rate Limiting

- Upload endpoints: 20 requests/hour
- Summary endpoints: 20 requests/hour
- Plot endpoints: 30 requests/hour
- Session endpoints: 30 requests/hour
- Health endpoints: 60 requests/hour (simple: 120 requests/hour)
- Other endpoints: 10-30 requests/hour

---

## Core Endpoints

### 1. File Upload

#### `POST /upload/`

Upload a CSV or Excel file for analysis.

**Parameters:**

- `file` (UploadFile, required): The file to upload
- `include_sample` (bool, optional): Include sample data in response (default: false)
- `encoding` (str, optional): File encoding for CSV files (auto-detected if not specified)

**Supported File Types:**

- CSV files (.csv)
- Excel files (.xlsx)

**Example Request:**

```bash
curl -X POST "http://localhost:8000/upload/" \
  -F "file=@data.csv" \
  -F "include_sample=true" \
  -F "encoding=utf-8"
```

**Example Response (200 OK):**

```json
{
  "message": "File uploaded successfully",
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "data.csv",
  "filetype": "CSV",
  "metadata": {
    "row_count": 1000,
    "column_count": 5,
    "columns": ["name", "age", "salary", "department", "hire_date"],
    "memory_estimate": {
      "total_bytes": 1048576,
      "total_mb": 1.0,
      "per_column": {
        "name": 262144,
        "age": 131072,
        "salary": 131072,
        "department": 196608,
        "hire_date": 327680
      }
    },
    "data_types": {
      "name": {
        "dtype": "object",
        "category": "O",
        "non_null_count": 1000,
        "null_count": 0,
        "unique_count": 1000
      },
      "age": {
        "dtype": "int64",
        "category": "i",
        "non_null_count": 1000,
        "null_count": 0,
        "unique_count": 45
      }
    },
    "processing_time_seconds": 0.245
  },
  "sample_data": {
    "name": ["John Doe", "Jane Smith", "Bob Johnson"],
    "age": [25, 30, 35],
    "salary": [50000, 60000, 70000]
  }
}
```

**Error Responses:**

**400 Bad Request - Invalid File:**

```json
{
  "detail": "File size exceeds maximum limit of 100MB"
}
```

**400 Bad Request - Unsupported File Type:**

```json
{
  "detail": "Unsupported file type. Only CSV and Excel files are supported."
}
```

**500 Internal Server Error:**

```json
{
  "detail": "An unexpected error occurred while processing the file. Please try again."
}
```

---

### 2. Data Summary

#### `GET /summary/`

Generate comprehensive statistical summary of the dataset.

**Parameters:**

- `session_id` (str, required): Unique session ID
- `include_categorical` (bool, optional): Include categorical column statistics (default: false)
- `include_correlation` (bool, optional): Include correlation matrix for numeric columns (default: false)
- `include_quality` (bool, optional): Include data quality metrics (default: false)
- `columns` (str, optional): Comma-separated list of specific columns to analyze

**Example Request:**

```bash
curl "http://localhost:8000/summary/?session_id=123e4567-e89b-12d3-a456-426614174000&include_categorical=true&include_correlation=true&include_quality=true"
```

**Example Response (200 OK):**

```json
{
  "filename": "data.csv",
  "filetype": "CSV",
  "row_count": 1000,
  "column_count": 5,
  "numeric_columns": 2,
  "categorical_columns": 3,
  "summary": {
    "numeric_summary": {
      "age": {
        "mean": 35.5,
        "median": 35.0,
        "std": 8.2,
        "min": 22,
        "max": 65,
        "count": 1000,
        "missing": 0,
        "percent_missing": 0.0,
        "percentile_25": 29.0,
        "percentile_75": 42.0
      },
      "salary": {
        "mean": 55000.0,
        "median": 52000.0,
        "std": 15000.0,
        "min": 30000,
        "max": 120000,
        "count": 1000,
        "missing": 0,
        "percent_missing": 0.0,
        "percentile_25": 42000.0,
        "percentile_75": 68000.0
      }
    },
    "categorical_summary": {
      "name": {
        "unique_count": 1000,
        "most_common_value": "John Doe",
        "most_common_count": 1,
        "count": 1000,
        "missing": 0,
        "percent_missing": 0.0,
        "data_type": "object"
      },
      "department": {
        "unique_count": 5,
        "most_common_value": "Engineering",
        "most_common_count": 300,
        "count": 1000,
        "missing": 0,
        "percent_missing": 0.0,
        "data_type": "object"
      }
    },
    "correlation_matrix": {
      "columns": ["age", "salary"],
      "correlation_matrix": {
        "age": {"age": 1.0, "salary": 0.75},
        "salary": {"age": 0.75, "salary": 1.0}
      }
    },
    "data_quality": {
      "name": {
        "total_values": 1000,
        "missing_values": 0,
        "percent_missing": 0.0,
        "data_quality": "excellent"
      },
      "age": {
        "total_values": 1000,
        "missing_values": 0,
        "percent_missing": 0.0,
        "data_quality": "excellent"
      }
    }
  },
  "warnings": [],
  "processing_time_seconds": 0.156
}
```

**Error Responses:**

**404 Not Found - Session Not Found:**

```json
{
  "detail": "Session 'invalid-session-id' not found"
}
```

**400 Bad Request - Invalid Columns:**

```json
{
  "detail": "Columns not found: invalid_column"
}
```

---

### 3. Data Visualization

#### `GET /plot/`

Generate various types of plots for data visualization.

**Parameters:**

- `session_id` (str, required): Unique session ID
- `column` (str, required): Column to plot
- `plot_type` (str, optional): Type of plot - histogram, boxplot, scatter, line (default: histogram)
- `y_column` (str, optional): Y-axis column for scatter/line plots
- `bins` (int, optional): Number of bins for histogram (default: 20)
- `color` (str, optional): Plot color (default: skyblue)
- `fig_width` (int, optional): Figure width (default: 8)
- `fig_height` (int, optional): Figure height (default: 6)
- `missing_strategy` (str, optional): How to handle missing values - skip, fill_mean, fill_median (default: skip)

**Example Request:**

```bash
curl "http://localhost:8000/plot/?session_id=123e4567-e89b-12d3-a456-426614174000&column=age&plot_type=histogram&bins=30&color=blue"
```

**Example Response (200 OK):**
Returns a PNG image of the plot.

**Example Request for Scatter Plot:**

```bash
curl "http://localhost:8000/plot/?session_id=123e4567-e89b-12d3-a456-426614174000&column=age&plot_type=scatter&y_column=salary&color=red"
```

**Error Responses:**

**404 Not Found - Session Not Found:**

```json
{
  "detail": "Session 'invalid-session-id' not found"
}
```

**400 Bad Request - Column Not Found:**

```json
{
  "detail": "Column 'invalid_column' not found in dataset. Available columns: age, salary, department"
}
```

**400 Bad Request - Non-numeric Column:**

```json
{
  "detail": "Column 'department' is not numeric (type: object) and cannot be plotted. Only numeric columns can be visualized with histograms."
}
```

---

### 4. Session Management

#### `GET /sessions/`

List all active sessions.

**Example Request:**

```bash
curl "http://localhost:8000/sessions/"
```

**Example Response (200 OK):**

```json
{
  "total_sessions": 3,
  "sessions": [
    {
      "session_id": "123e4567-e89b-12d3-a456-426614174000",
      "filename": "data.csv",
      "filetype": "CSV",
      "upload_time": "2024-01-15T10:30:00Z",
      "last_access_time": "2024-01-15T11:45:00Z",
      "row_count": 1000,
      "column_count": 5,
      "memory_usage_mb": 2.5
    },
    {
      "session_id": "456e7890-e89b-12d3-a456-426614174001",
      "filename": "sales.xlsx",
      "filetype": "XLSX",
      "upload_time": "2024-01-15T09:15:00Z",
      "last_access_time": "2024-01-15T10:20:00Z",
      "row_count": 500,
      "column_count": 8,
      "memory_usage_mb": 1.8
    }
  ],
  "processing_time_seconds": 0.023
}
```

#### `DELETE /sessions/{session_id}`

Delete a specific session.

**Example Request:**

```bash
curl -X DELETE "http://localhost:8000/sessions/123e4567-e89b-12d3-a456-426614174000"
```

**Example Response (200 OK):**

```json
{
  "message": "Session 123e4567-e89b-12d3-a456-426614174000 deleted successfully",
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "data.csv",
  "processing_time_seconds": 0.012
}
```

**Error Responses:**

**404 Not Found - Session Not Found:**

```json
{
  "detail": "Session 'invalid-session-id' not found"
}
```

---

### 5. Column Analysis

#### `GET /columns/{session_id}`

Get detailed metadata for columns.

**Parameters:**

- `session_id` (str, required): Unique session ID
- `column` (str, optional): Specific column to analyze (if None, returns all columns)

**Example Request:**

```bash
curl "http://localhost:8000/columns/123e4567-e89b-12d3-a456-426614174000?column=age"
```

**Example Response (200 OK):**

```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "data.csv",
  "total_columns": 5,
  "metadata": {
    "column_name": "age",
    "data_type": "int64",
    "data_category": "i",
    "total_values": 1000,
    "non_null_count": 1000,
    "null_count": 0,
    "null_percentage": 0.0,
    "unique_count": 45,
    "unique_percentage": 4.5,
    "min": 22,
    "max": 65,
    "mean": 35.5,
    "median": 35.0,
    "std": 8.2,
    "percentile_25": 29.0,
    "percentile_75": 42.0,
    "sample_values": [25, 30, 35, 28, 42]
  },
  "processing_time_seconds": 0.034
}
```

**Error Responses:**

**404 Not Found - Session Not Found:**

```json
{
  "detail": "Session 'invalid-session-id' not found"
}
```

**400 Bad Request - Column Not Found:**

```json
{
  "detail": "Column 'invalid_column' not found in dataset. Available columns: age, salary, department"
}
```

---

### 6. Missing Value Analysis

#### `GET /missing-values/{session_id}`

Get comprehensive missing value report.

**Example Request:**

```bash
curl "http://localhost:8000/missing-values/123e4567-e89b-12d3-a456-426614174000"
```

**Example Response (200 OK):**

```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "data.csv",
  "report": {
    "total_rows": 1000,
    "total_columns": 5,
    "columns_with_missing": ["salary"],
    "missing_summary": {
      "name": {
        "missing_count": 0,
        "missing_percent": 0.0,
        "non_missing_count": 1000,
        "data_type": "object",
        "quality_rating": "excellent"
      },
      "salary": {
        "missing_count": 50,
        "missing_percent": 5.0,
        "non_missing_count": 950,
        "data_type": "int64",
        "quality_rating": "excellent"
      }
    },
    "missing_patterns": {
      "salary": "low_missing"
    },
    "recommendations": [
      "Consider imputation strategies for columns with 20-50% missing values: salary"
    ]
  },
  "statistics": {
    "overall": {
      "total_cells": 5000,
      "missing_cells": 50,
      "missing_percentage": 1.0
    },
    "by_column": {
      "name": {
        "missing_count": 0,
        "missing_percentage": 0.0,
        "non_missing_count": 1000
      },
      "salary": {
        "missing_count": 50,
        "missing_percentage": 5.0,
        "non_missing_count": 950
      }
    },
    "by_row": {
      "rows_with_missing": 50,
      "rows_without_missing": 950,
      "rows_all_missing": 0
    }
  },
  "processing_time_seconds": 0.078
}
```

#### `POST /missing-values/{session_id}/handle`

Handle missing values with specified strategy.

**Parameters:**

- `session_id` (str, required): Unique session ID
- `strategy` (str, required): Strategy to handle missing values
  - `skip`: Drop rows with missing values
  - `fill_mean`: Fill with mean (numeric) or mode (categorical)
  - `fill_median`: Fill with median (numeric) or mode (categorical)
  - `fill_mode`: Fill with most common value
  - `forward_fill`: Forward fill
  - `backward_fill`: Backward fill
- `columns` (str, optional): Comma-separated list of columns to process

**Example Request:**

```bash
curl -X POST "http://localhost:8000/missing-values/123e4567-e89b-12d3-a456-426614174000/handle?strategy=fill_mean&columns=salary"
```

**Example Response (200 OK):**

```json
{
  "message": "Missing values handled successfully using fill_mean strategy",
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "strategy": "fill_mean",
  "columns_processed": ["salary"],
  "original_statistics": {
    "overall": {
      "total_cells": 5000,
      "missing_cells": 50,
      "missing_percentage": 1.0
    }
  },
  "processed_statistics": {
    "overall": {
      "total_cells": 5000,
      "missing_cells": 0,
      "missing_percentage": 0.0
    }
  },
  "processing_time_seconds": 0.045
}
```

---

### 7. Data Export

#### `GET /export/{session_id}`

Export processed data in CSV or JSON format.

**Parameters:**

- `session_id` (str, required): Unique session ID
- `format` (str, optional): Export format - csv or json (default: csv)
- `columns` (str, optional): Comma-separated list of columns to export
- `rows` (int, optional): Number of rows to export

**Example Request:**

```bash
curl "http://localhost:8000/export/123e4567-e89b-12d3-a456-426614174000?format=csv&columns=name,age,salary&rows=100"
```

**Example Response (200 OK):**
Returns a CSV file with the specified data.

**Example Request for JSON:**

```bash
curl "http://localhost:8000/export/123e4567-e89b-12d3-a456-426614174000?format=json"
```

**Error Responses:**

**404 Not Found - Session Not Found:**

```json
{
  "detail": "Session 'invalid-session-id' not found"
}
```

**400 Bad Request - Invalid Format:**

```json
{
  "detail": "Invalid format. Supported formats: csv, json"
}
```

---

### 8. Health Monitoring

#### `GET /health/`

Comprehensive health check endpoint.

**Example Request:**

```bash
curl "http://localhost:8000/health/"
```

**Example Response (200 OK):**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:00:00Z",
  "uptime_seconds": 3600.5,
  "system": {
    "cpu": {
      "percent": 15.2,
      "count": 8,
      "status": "healthy"
    },
    "memory": {
      "total_gb": 16.0,
      "available_gb": 12.5,
      "used_gb": 3.5,
      "percent": 21.9,
      "status": "healthy"
    },
    "disk": {
      "total_gb": 500.0,
      "free_gb": 400.0,
      "used_gb": 100.0,
      "percent": 20.0,
      "status": "healthy"
    },
    "process": {
      "memory_mb": 45.2,
      "memory_percent": 0.3,
      "cpu_percent": 2.1
    }
  },
  "api": {
    "active_sessions": 3,
    "total_session_memory_mb": 5.8,
    "session_details": [
      {
        "session_id": "123e4567-e89b-12d3-a456-426614174000",
        "filename": "data.csv",
        "row_count": 1000,
        "memory_mb": 2.5
      }
    ],
    "status": "healthy"
  },
  "application": {
    "uptime_seconds": 3600.5,
    "uptime_hours": 1.0,
    "python_version": "3.11.0",
    "pid": 12345,
    "status": "healthy"
  },
  "health_indicators": ["All systems operational"],
  "processing_time_seconds": 0.089
}
```

#### `GET /health/simple`

Simple health check for basic monitoring.

**Example Request:**

```bash
curl "http://localhost:8000/health/simple"
```

**Example Response (200 OK):**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:00:00Z",
  "active_sessions": 3,
  "memory_usage_percent": 21.9,
  "disk_usage_percent": 20.0
}
```

---

## Error Handling

### Common Error Responses

#### 400 Bad Request

```json
{
  "detail": "Invalid request parameters"
}
```

#### 404 Not Found

```json
{
  "detail": "Resource not found"
}
```

#### 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "loc": ["query", "session_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 429 Too Many Requests

```json
{
  "detail": "Rate limit exceeded"
}
```

#### 500 Internal Server Error

```json
{
  "detail": "An unexpected error occurred. Please try again."
}
```

---

## Data Types and Constraints

### File Upload Constraints

- **Maximum file size**: 100MB
- **Supported formats**: CSV, XLSX
- **Minimum rows**: 1
- **Maximum rows**: 1,000,000
- **Minimum columns**: 1
- **Maximum columns**: 500

### Session Management

- **Session timeout**: 1 hour of inactivity
- **Maximum sessions**: 200 per instance
- **Session cleanup**: Automatic every 10 minutes

### Rate Limiting

- **Upload**: 20 requests/hour
- **Summary**: 20 requests/hour
- **Plot**: 30 requests/hour
- **Sessions**: 30 requests/hour
- **Health**: 60 requests/hour (simple: 120 requests/hour)

---

## Best Practices

### File Preparation

1. Ensure CSV files have proper headers
2. Use consistent data types within columns
3. Handle missing values appropriately
4. Use UTF-8 encoding for international characters

### Performance Optimization

1. Use column filtering for large datasets
2. Sample data for initial exploration
3. Delete unused sessions regularly
4. Monitor memory usage via health endpoint

### Error Handling

1. Always check response status codes
2. Handle rate limiting gracefully
3. Implement retry logic for transient errors
4. Validate session IDs before making requests

---

## Examples

### Complete Workflow Example

1. **Upload a file:**

```bash
curl -X POST "http://localhost:8000/upload/" -F "file=@data.csv"
```

2. **Get summary statistics:**

```bash
curl "http://localhost:8000/summary/?session_id=YOUR_SESSION_ID&include_categorical=true"
```

3. **Generate a plot:**

```bash
curl "http://localhost:8000/plot/?session_id=YOUR_SESSION_ID&column=age&plot_type=histogram"
```

4. **Export processed data:**

```bash
curl "http://localhost:8000/export/YOUR_SESSION_ID?format=csv"
```

5. **Clean up session:**

```bash
curl -X DELETE "http://localhost:8000/sessions/YOUR_SESSION_ID"
```

This documentation provides comprehensive information for using the Data Summary API effectively in production environments.
