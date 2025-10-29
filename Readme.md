# Data Summary API

A comprehensive data analysis API that provides statistical summaries, visualizations, and data management capabilities for uploaded datasets.

## 🚀 Features

- **File Upload**: Support for CSV and Excel files with automatic encoding detection
- **Statistical Analysis**: Comprehensive summary statistics including numeric and categorical analysis
- **Data Visualization**: Multiple plot types (histogram, boxplot, scatter, line) with customization options
- **Session Management**: Track and manage multiple data analysis sessions
- **Missing Value Handling**: Advanced missing value analysis and imputation strategies
- **Data Export**: Export processed data in CSV or JSON formats
- **Health Monitoring**: Comprehensive health checks for production monitoring

## 📋 Quick Start

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd data_summary_api
```

2. Create and activate virtual environment:

```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the application:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Interactive Documentation

Once the server is running, you can access:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 📚 API Documentation

### Core Endpoints

| Endpoint                      | Method | Description                  |
| ----------------------------- | ------ | ---------------------------- |
| `/upload/`                    | POST   | Upload CSV/Excel files       |
| `/summary/`                   | GET    | Get statistical summary      |
| `/plot/`                      | GET    | Generate data visualizations |
| `/sessions/`                  | GET    | List active sessions         |
| `/sessions/{id}`              | DELETE | Delete specific session      |
| `/columns/{id}`               | GET    | Get column metadata          |
| `/missing-values/{id}`        | GET    | Get missing value report     |
| `/missing-values/{id}/handle` | POST   | Handle missing values        |
| `/export/{id}`                | GET    | Export processed data        |
| `/health/`                    | GET    | Comprehensive health check   |
| `/health/simple`              | GET    | Simple health check          |

### Example Usage

#### 1. Upload a File

```bash
curl -X POST "http://localhost:8000/upload/" \
  -F "file=@data.csv" \
  -F "include_sample=true"
```

#### 2. Get Summary Statistics

```bash
curl "http://localhost:8000/summary/?session_id=YOUR_SESSION_ID&include_categorical=true&include_correlation=true"
```

#### 3. Generate a Plot

```bash
curl "http://localhost:8000/plot/?session_id=YOUR_SESSION_ID&column=age&plot_type=histogram&bins=30"
```

#### 4. Export Data

```bash
curl "http://localhost:8000/export/YOUR_SESSION_ID?format=csv&columns=name,age,salary"
```

## 🔧 Configuration

### Rate Limiting

- Upload endpoints: 20 requests/hour
- Summary endpoints: 20 requests/hour
- Plot endpoints: 30 requests/hour
- Session endpoints: 30 requests/hour
- Health endpoints: 60 requests/hour (simple: 120 requests/hour)

### File Constraints

- **Maximum file size**: 100MB
- **Supported formats**: CSV, XLSX
- **Minimum rows**: 1
- **Maximum rows**: 1,000,000
- **Minimum columns**: 1
- **Maximum columns**: 500

### Session Management

- Sessions expire after 1 hour of inactivity
- Maximum 200 sessions per instance
- Automatic cleanup every 10 minutes

## 📊 Data Types and Analysis

### Numeric Statistics

- Mean, median, standard deviation
- Min, max, percentiles (25th, 75th)
- Missing value counts and percentages
- Correlation matrix for multiple numeric columns

### Categorical Statistics

- Unique value counts
- Most common values and frequencies
- Data type information
- Missing value analysis

### Data Quality Metrics

- Missing value percentages per column
- Data quality ratings (excellent, good, fair, poor)
- Recommendations for data cleaning

## 🎨 Visualization Options

### Plot Types

- **Histogram**: Distribution of numeric data
- **Boxplot**: Statistical summary with outliers
- **Scatter Plot**: Relationship between two numeric variables
- **Line Plot**: Trends over time or ordered data

### Customization Options

- Colors, figure size, bins
- Missing value handling strategies
- Multiple column plotting

## 🔍 Missing Value Handling

### Analysis

- Comprehensive missing value reports
- Pattern detection (high, moderate, low missing)
- Quality recommendations

### Imputation Strategies

- **Skip**: Drop rows with missing values
- **Fill Mean**: Fill with mean (numeric) or mode (categorical)
- **Fill Median**: Fill with median (numeric) or mode (categorical)
- **Fill Mode**: Fill with most common value
- **Forward Fill**: Propagate last valid observation
- **Backward Fill**: Use next valid observation

## 🏥 Health Monitoring

### Comprehensive Health Check (`/health/`)

- System metrics (CPU, memory, disk)
- API metrics (active sessions, memory usage)
- Application metrics (uptime, version)
- Health status indicators

### Simple Health Check (`/health/simple`)

- Basic status for load balancers
- Essential metrics only
- Fast response time

## 🚨 Error Handling

The API provides comprehensive error handling with detailed error messages:

- **400 Bad Request**: Invalid parameters or file constraints
- **404 Not Found**: Session or resource not found
- **422 Unprocessable Entity**: Validation errors
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Unexpected errors

## 📈 Performance Considerations

### Large File Handling

- Chunked reading for files over 10MB
- Optional sampling for initial exploration
- Memory-efficient processing
- Stream processing for exports

### Optimization Tips

- Use column filtering for large datasets
- Sample data for initial exploration
- Delete unused sessions regularly
- Monitor memory usage via health endpoint

## 🔒 Security

- Rate limiting to prevent abuse
- File size and type validation
- Input sanitization
- Comprehensive error handling

## 📝 Logging

The API includes structured logging with:

- Request/response logging
- Performance metrics
- Error tracking
- Session management events

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Email: <support@datasummaryapi.com>
- Documentation: [API Documentation](API_DOCUMENTATION.md)
- Interactive docs: `http://localhost:8000/docs`

## 🔄 Changelog

### Version 1.0.0

- Initial release with comprehensive data analysis features
- Support for CSV and Excel files
- Statistical analysis and visualization
- Session management and data export
- Health monitoring and error handling
