# Architecture Guide

## Project Overview

This cryptocurrency data pipeline demonstrates a production-grade ETL system for collecting, processing, and analyzing real-time crypto market data from Coinbase.

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Data Pipeline                             │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │   EXTRACT    │───▶│  TRANSFORM   │───▶│    LOAD      │   │
│  │              │    │              │    │              │   │
│  │ • API calls  │    │ • Validation │    │ • SQLite     │   │
│  │ • Retry logic│    │ • Indicators │    │ • Schema mgt │   │
│  │ • Error hdlg │    │ • Normalization   │ • Indexes    │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │
│         ▲                    ▲                    ▲           │
│         │                    │                    │           │
│    Logging & Config, Exception Handling, Caching            │
│                                                               │
└──────────────────────────────────────────────────────────────┘
         │
         │
    ┌────▼─────────────────────────────────────┐
    │    Analysis & Visualization              │
    ├─────────────────────────────────────────┤
    │  • Price history charts                  │
    │  • Technical indicators (SMA, RSI)       │
    │  • Multi-product comparisons             │
    │  • Statistical metrics & anomaly detect  │
    └─────────────────────────────────────────┘
```

## Module Responsibilities

### Core Pipeline Modules (`scripts/`)

#### `extract.py`
- Fetches ticker data from Coinbase public API
- Implements retry logic with exponential backoff
- Handles rate limiting and connection errors
- Creates reusable HTTP session with automatic retries

**Key Functions:**
- `fetch_coinbase_ticker(product_id)`: Fetch current ticker for a product

#### `transform.py`
- Validates incoming data against required schema
- Transforms raw API responses to normalized DataFrames
- Calculates technical indicators (SMA, RSI)
- Computes spread metrics (bid-ask spread, spread %)

**Key Functions:**
- `transform_ticker(raw)`: Transform and validate ticker data
- `add_technical_indicators(df)`: Add SMA and RSI columns

#### `load.py`
- Manages SQLite database connections and schema
- Creates optimized table structure with indexes
- Handles data insertion with duplicate detection
- Provides query interface for analytics

**Key Functions:**
- `store_to_db(df)`: Insert transformed data
- `get_latest_data(product_id)`: Retrieve historical data
- `get_connection()`: Get database connection

#### `visualize.py`
- Generates price history charts with technical indicators
- Creates multi-product comparison plots
- Calculates statistical metrics (volatility, correlation, etc.)
- Exports charts to PNG files

**Key Functions:**
- `plot_price_history(product_id)`: Generate single product chart
- `plot_multi_product_comparison(product_ids)`: Compare multiple products
- `get_price_statistics(product_id)`: Calculate metrics

### Infrastructure Modules

#### `config.py`
- Central configuration management using Pydantic
- Environment variable support with .env file
- Type-safe settings with validation
- Sensible defaults for development

**Key Settings:**
- API configuration (timeout, retries, base URL)
- Database configuration (path, echo mode)
- Logging configuration (level, format, file path)
- Collection parameters (pairs, intervals)

#### `logger_config.py`
- Structured logging with both console and file output
- Automatic log directory creation
- Rotating file handler (10MB max per file, 5 backups)
- Module-level logger instances

#### `exceptions.py`
- Custom exception hierarchy for better error handling
- Specific exception types for different failure modes
- Enables targeted error recovery strategies

**Exception Types:**
- `PipelineException`: Base exception
- `APIException`: API-specific errors
- `TransformException`: Data transformation errors
- `LoadException`: Database operation errors
- `ValidationException`: Data validation errors

#### `cache.py`
- Simple in-memory cache with TTL support
- Optional decorator for function result caching
- Reduces redundant API calls

## Database Schema

### `prices` Table

```sql
CREATE TABLE prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    price REAL NOT NULL,
    size REAL NOT NULL,
    bid REAL NOT NULL,
    ask REAL NOT NULL,
    spread REAL,
    spread_pct REAL,
    time TIMESTAMP NOT NULL UNIQUE,
    trade_id INTEGER,
    sma_20 REAL,
    sma_50 REAL,
    rsi_14 REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for query optimization
CREATE INDEX idx_product_id ON prices(product_id);
CREATE INDEX idx_time ON prices(time DESC);
CREATE INDEX idx_product_time ON prices(product_id, time DESC);
```

**Schema Design Rationale:**
- `UNIQUE` constraint on `time` column prevents duplicate entries
- Composite index `(product_id, time DESC)` optimizes common queries
- `spread` and `spread_pct` precomputed for efficiency
- Technical indicator columns enable historical analysis
- `created_at` timestamp for audit trail

## Data Flow

1. **Extract Phase**
   - API request to Coinbase public endpoint
   - Automatic retry on transient failures
   - Rate limit detection and backoff
   - Response validation

2. **Transform Phase**
   - Schema validation (required fields, data types)
   - Type normalization (strings → floats/datetimes)
   - Calculated fields (spread, spread %)
   - Optional technical indicators

3. **Load Phase**
   - Database connection with automatic schema creation
   - Duplicate detection via UNIQUE constraint
   - Transaction management
   - Insert confirmation and logging

4. **Analysis Phase**
   - Historical data retrieval
   - Statistical calculations
   - Chart generation
   - Anomaly detection

## Error Handling Strategy

### By Layer

**Extract:** 
- Retry logic for transient failures
- Rate limit detection
- Timeout handling
- Connection error recovery

**Transform:**
- Input validation
- Type checking
- Range validation
- Missing field detection

**Load:**
- Duplicate detection
- Schema migration
- Transaction rollback
- Data integrity checks

### Error Recovery

- Graceful degradation (skip single product, continue pipeline)
- Comprehensive logging for debugging
- Custom exception types for targeted recovery
- Fail-fast on critical errors, retry on transient

## Scalability Considerations

### Current Design
- Single-threaded sequential processing
- In-memory caching reduces API calls
- Indexed database for fast queries
- Minimal memory footprint

### Potential Improvements
1. **Async/Concurrent:**
   - Multi-product fetch in parallel
   - Non-blocking API calls with `asyncio`
   - Connection pooling

2. **Database:**
   - Time-series database (InfluxDB, TimescaleDB)
   - Partitioning by date for large datasets
   - Read replicas for analytics queries

3. **Deployment:**
   - Containerized with Docker
   - Kubernetes orchestration
   - Distributed task scheduler (Celery, Prefect)
   - Message queue (Kafka, RabbitMQ)

4. **Analytics:**
   - Data warehouse (Snowflake, BigQuery)
   - Real-time streaming (Kafka Streams, Spark)
   - Machine learning pipelines

## Security Considerations

1. **API Security:**
   - No hardcoded credentials
   - Environment variable configuration
   - Request timeouts prevent hanging
   - Rate limit compliance

2. **Database:**
   - Parameterized queries (pandas handles this)
   - No direct SQL injection vectors
   - File-based encryption for sensitive data

3. **Code:**
   - Input validation on all inputs
   - Error messages don't leak sensitive info
   - Comprehensive logging (audit trail)
   - Dependency version pinning

## Testing Strategy

- **Unit Tests:** Isolated module testing with mocks
- **Integration Tests:** End-to-end pipeline validation
- **Coverage Target:** 80%+ code coverage
- **Fixtures:** Reusable test data and database

See `tests/test_pipeline.py` for comprehensive test suite.

