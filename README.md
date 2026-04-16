# Coinbase Crypto Data Engineering Pipeline

A production-focused ETL pipeline that collects live market ticker data from Coinbase, validates and enriches it, stores it in SQLite, and produces analysis-ready charts and metrics.

## Why This Is Employer-Friendly

- Clear ETL separation: `extract` -> `transform` -> `load`
- Resilience patterns: retries, timeouts, structured exceptions
- Production basics: central config, rotating logs, Docker, CI workflow
- Data engineering mindset: schema evolution support and indexing
- Analytics value: spread metrics and rolling indicators (SMA/RSI)

## Implemented Upgrades

- Multi-product ingestion (`BTC-USD`, `ETH-USD`, `SOL-USD` by default)
- CLI pipeline orchestration in `main.py`
- Robust API client in `scripts/extract.py` (retry + error handling)
- Validation/enrichment in `scripts/transform.py`
- Improved DB layer in `scripts/load.py` (schema creation, migration guardrails, indexed queries)
- Visualization/statistics utilities in `scripts/visualize.py`
- Project-level modules: `config.py`, `logger_config.py`, `exceptions.py`, `cache.py`
- Test suite scaffold in `tests/test_pipeline.py`
- DevOps assets: `Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml`
- Documentation: `docs/ARCHITECTURE.md`, `docs/DEPLOYMENT.md`
- Data maintenance utility: `scripts/cleanup_db.py`
- Recruiter/demo API: `dashboard_api.py`
- Always-on collector mode: `main.py --daemon`

## Project Structure

```text
coinbase-crypto-data-pipeline/
  main.py
  config.py
  logger_config.py
  exceptions.py
  cache.py
  scripts/
	extract.py
	transform.py
	load.py
	visualize.py
  tests/
  docs/
  Dockerfile
  docker-compose.yml
```

## Quick Start (Windows PowerShell)

```powershell
Set-Location "C:\Users\big_j\PycharmProjects\coinbase-crypto-data-pipeline"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py --products BTC-USD ETH-USD SOL-USD --stats --plot
```

## Useful Commands

```powershell
# Pull latest data for default configured pairs
python main.py

# Pull specific assets and print statistics
python main.py --products BTC-USD ETH-USD --stats

# Generate charts into data/
python main.py --products BTC-USD --plot

# Run collector mode for 3 cycles (demo-safe)
python main.py --products BTC-USD ETH-USD SOL-USD --daemon --interval 30 --max-runs 3

# Preview DB cleanup impact
python -m scripts.cleanup_db --dry-run

# Perform cleanup and compact DB
python -m scripts.cleanup_db --vacuum

# Start recruiter-facing metrics API
uvicorn dashboard_api:app --reload

# Run tests
pytest tests -v
```

## Recruiter-Facing API

Once the API is running, useful endpoints are:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod "http://127.0.0.1:8000/dashboard/metrics?products=BTC-USD&products=ETH-USD"
```

The API is intentionally read-only and designed for demos/interviews:

- `GET /health` → pipeline/storage health snapshot
- `GET /dashboard/metrics` → DB summary + product-level JSON metrics

## Database Cleanup Utility

The cleanup command removes unlabeled legacy rows, optionally removes `UNKNOWN` rows, and de-duplicates `(product_id, time)` records.

```powershell
python -m scripts.cleanup_db --dry-run
python -m scripts.cleanup_db --keep-unknown
python -m scripts.cleanup_db --vacuum
```

## Scheduled Collector Mode

Use daemon mode to simulate an always-on ingestion service for demos:

```powershell
python main.py --daemon
python main.py --products BTC-USD ETH-USD SOL-USD --daemon --interval 60
python main.py --products BTC-USD --daemon --interval 10 --max-runs 5
```

## Notes

- This pipeline uses Coinbase public market endpoints and does not require `cdp_api_key.json`.
- Runtime behavior (charts/data volume) depends on your local DB contents and network availability.
- If you already have an older `prices` table, the loader includes compatibility logic for legacy schema transitions.

## Next Portfolio Enhancements

- Add scheduled execution (Task Scheduler/cron) with retention policies
- Expose a small FastAPI read API for recent metrics
- Add data quality checks and test coverage reporting badge from CI
- Add a dashboard layer (Plotly/Streamlit) for interviewer demos
