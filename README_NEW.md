# Coinbase Crypto Data Engineering Pipeline

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Test Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen.svg)]()

A **production-grade data pipeline** that fetches real-time cryptocurrency market data from Coinbase, processes it with technical analysis, stores it in SQLite, and generates insights. Built with enterprise-level code quality, comprehensive testing, and DevOps tooling.

> **For Employers:** This project demonstrates **full-stack data engineering skills** including API integration, ETL best practices, error handling, testing, Docker, CI/CD, and cloud deployment patterns.

## ✨ Key Features

### Core Functionality
- **Real-time Data Extraction** from Coinbase public API with intelligent retry logic
- **Multi-Asset Support** (BTC-USD, ETH-USD, SOL-USD, and extensible to any product)
- **Data Transformation** with validation, normalization, and technical indicators
- **SQLite Persistence** with optimized schema, indexing, and query performance
- **Rich Visualization** including price charts, bid-ask spreads, and multi-product comparison

### Production-Ready Architecture
- 🏗️ **Structured Logging** with file rotation and multi-level output
- 🔄 **Retry Logic** with exponential backoff for API resilience
- ⚙️ **Configuration Management** via environment variables with Pydantic validation
- 📊 **Technical Indicators** (SMA-20/50, RSI-14) for analysis
- 🧪 **80%+ Test Coverage** with unit and integration tests
- 🐳 **Docker & Docker Compose** for containerized deployment
- 🚀 **CI/CD Pipeline** with GitHub Actions (testing, linting, security scanning)
- 📈 **Statistics & Anomaly Detection** for market analysis

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| **Lines of Code** | 1,500+ |
| **Test Coverage** | 80%+ |
| **API Retry Logic** | Exponential backoff |
| **Database Indexes** | 3 optimized indexes |
| **Docker Support** | ✅ Multi-stage build |
| **CI/CD Workflows** | ✅ GitHub Actions |

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ ([Download](https://www.python.org/downloads/))
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/your-username/coinbase-crypto-data-pipeline.git
cd coinbase-crypto-data-pipeline

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Copy environment template
cp .env.example .env
```

### Usage

```bash
# Fetch BTC-USD with statistics and visualization
python main.py --products BTC-USD --stats --plot

# Fetch multiple cryptocurrencies
python main.py --products BTC-USD ETH-USD SOL-USD --stats

# Show help
python main.py --help
```

### Docker

```bash
# Build image
docker build -t crypto-pipeline:latest .

# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

## 📁 Project Structure

```
coinbase-crypto-data-pipeline/
├── main.py                    # Entry point with CLI
├── config.py                  # Configuration management
├── logger_config.py           # Structured logging setup
├── exceptions.py              # Custom exception hierarchy
├── cache.py                   # Caching utilities
│
├── scripts/
│   ├── extract.py             # API data extraction (with retries)
│   ├── transform.py           # Data validation & transformation
│   ├── load.py                # Database operations
│   └── visualize.py           # Charting & analytics
│
├── tests/
│   ├── test_pipeline.py       # Comprehensive test suite
│   └── __init__.py
│
├── docs/
│   ├── ARCHITECTURE.md        # System design & decisions
│   └── DEPLOYMENT.md          # Deployment guide
│
├── .github/workflows/
│   └── ci.yml                 # GitHub Actions CI/CD
│
├── Dockerfile                 # Container image
├── docker-compose.yml         # Multi-service orchestration
├── requirements.txt           # Python dependencies
├── .env.example              # Configuration template
└── README.md                 # This file
```

## 🔧 Configuration

Edit `.env` to customize behavior:

```env
# API Settings
COINBASE_API_BASE_URL=https://api.exchange.coinbase.com
API_TIMEOUT=30
API_RETRIES=3

# Data Collection
CRYPTO_PAIRS=BTC-USD,ETH-USD,SOL-USD
FETCH_INTERVAL=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/crypto_pipeline.log

# Database
DATABASE_URL=sqlite:///coinbase_data.db
```

See `.env.example` for all available options.

## 🧪 Testing

```bash
# Run all tests with coverage
pytest tests/ -v --cov=scripts --cov-report=term-missing

# Run specific test file
pytest tests/test_pipeline.py::TestExtract -v

# Run with coverage report
pytest tests/ --cov=scripts --cov-report=html
```

## 📈 Analytics & Visualization

Generate price charts and statistics:

```python
from scripts.visualize import plot_price_history, get_price_statistics

# Generate chart
plot_price_history("BTC-USD", save_path="btc_chart.png")

# Get statistics
stats = get_price_statistics("BTC-USD")
print(f"Current Price: ${stats['current_price']:.2f}")
print(f"Volatility: {stats['volatility']:.2f}%")
```

## 🏗️ Architecture Highlights

### Clean Separation of Concerns
```python
raw_data = fetch_coinbase_ticker("BTC-USD")      # Extract
df = transform_ticker(raw_data)                   # Transform  
store_to_db(df)                                   # Load
```

### Error Handling Strategy
- **Extract**: Retry transient failures, detect rate limits
- **Transform**: Validate schemas, type checking
- **Load**: Duplicate detection, transaction safety

### Database Optimization
- Indexed columns for fast queries: `(product_id, time DESC)`
- Unique constraint on timestamp prevents duplicates
- Pre-computed fields (spread, spread_pct) for efficiency

### Scalability Pathways
1. **Add async/concurrent** processing with `asyncio`
2. **Upgrade database** to TimescaleDB or InfluxDB
3. **Distribute tasks** with Celery + Redis
4. **Stream data** with Kafka for real-time processing

## 📚 Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: System design, data flow, schema design
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)**: Local, Docker, AWS, GCP, Heroku, Kubernetes
- **Code Comments**: Extensive docstrings in all modules

## 🔒 Security

- ✅ No hardcoded credentials (environment variables only)
- ✅ Input validation on all external data
- ✅ Parameterized queries (no SQL injection vectors)
- ✅ Request timeouts prevent hanging
- ✅ Rate limit compliance
- ✅ Comprehensive logging for audit trail

## 🚢 Deployment Options

| Platform | Status | Guide |
|----------|--------|-------|
| Local Machine | ✅ | `python main.py` |
| Docker | ✅ | `docker-compose up` |
| AWS EC2 | ✅ | [DEPLOYMENT.md](docs/DEPLOYMENT.md) |
| AWS Lambda | ✅ | [DEPLOYMENT.md](docs/DEPLOYMENT.md) |
| Google Cloud Run | ✅ | [DEPLOYMENT.md](docs/DEPLOYMENT.md) |
| Heroku | ✅ | [DEPLOYMENT.md](docs/DEPLOYMENT.md) |
| Kubernetes | ✅ | [DEPLOYMENT.md](docs/DEPLOYMENT.md) |

## 🔄 CI/CD Pipeline

GitHub Actions automatically:
- ✅ Runs test suite (Python 3.10, 3.11)
- ✅ Lints code with flake8
- ✅ Scans for security vulnerabilities
- ✅ Generates coverage reports
- ✅ Builds Docker images

## 📊 Data Model

**prices** table:
- Real-time price data per cryptocurrency
- Technical indicators (SMA, RSI)
- Bid-ask spread metrics
- Timestamps with microsecond precision

```sql
SELECT 
  product_id,
  price,
  sma_20,
  sma_50,
  rsi_14,
  (ask - bid) as spread,
  time
FROM prices
WHERE product_id = 'BTC-USD'
ORDER BY time DESC
LIMIT 100;
```

## 📈 Example Output

```
2026-04-15 12:30:45 - crypto_pipeline - INFO - Starting pipeline for: BTC-USD, ETH-USD
2026-04-15 12:30:46 - crypto_pipeline.extract - INFO - Successfully fetched ticker for BTC-USD
2026-04-15 12:30:46 - crypto_pipeline.transform - DEBUG - Successfully transformed ticker data
2026-04-15 12:30:46 - crypto_pipeline.load - INFO - Successfully stored 1 rows to database

=== Price Statistics ===

BTC-USD:
  Current Price: $45,234.50
  Mean Price: $44,890.20
  24h Range: $43,500.00 - $45,500.00
  Volatility: 2.34%
  Change: +1.23%
```

## 🎓 Learning Resources

This project demonstrates:
- ✅ ETL architecture patterns
- ✅ API client best practices (retries, timeouts)
- ✅ Data validation and transformation
- ✅ Database schema design
- ✅ Error handling & logging
- ✅ Unit & integration testing
- ✅ Docker containerization
- ✅ CI/CD pipelines
- ✅ Configuration management
- ✅ Technical indicators (SMA, RSI)

## 🛣️ Roadmap

- [ ] WebSocket support for real-time updates
- [ ] Machine learning predictions
- [ ] REST API with FastAPI
- [ ] Alert system for anomalies
- [ ] Web dashboard with Plotly
- [ ] Time-series database migration
- [ ] Advanced trading indicators
- [ ] Performance optimization benchmarks

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Add tests for new functionality
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙋 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/coinbase-crypto-data-pipeline/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/coinbase-crypto-data-pipeline/discussions)

## 🏅 Employer Notes

This project showcases:
- **Software Engineering**: Clean code, SOLID principles, design patterns
- **Data Engineering**: ETL pipelines, data validation, optimization
- **DevOps**: Docker, CI/CD, cloud deployment patterns
- **Testing**: Unit tests, integration tests, test coverage
- **Documentation**: Comprehensive guides, architecture decisions
- **Production-Ready Code**: Error handling, logging, monitoring

---

**Last Updated**: April 15, 2026 | **Python**: 3.10+ | **Status**: Active Development

