"""Tests for cleanup utility, dashboard API, and collector mode."""

from __future__ import annotations

import sqlite3
from importlib import import_module
from pathlib import Path
from unittest.mock import patch

import pandas as pd

TestClient = import_module("fastapi.testclient").TestClient

import main as pipeline_main
from dashboard_api import app
from scripts.load import cleanup_database, get_database_summary


def seed_prices_table(db_path: Path) -> None:
    """Create a small test dataset with valid, invalid, and duplicate rows."""
    conn = sqlite3.connect(db_path)
    rows = [
        (70000.0, 1.0, 69999.0, 70001.0, "2026-04-15T12:00:00", "BTC-USD", 2.0, 0.0028, 1),
        (70000.0, 1.0, 69999.0, 70001.0, "2026-04-15T12:00:00", "BTC-USD", 2.0, 0.0028, 2),
        (2400.0, 2.0, 2399.0, 2401.0, "2026-04-15T12:01:00", "ETH-USD", 2.0, 0.0833, 3),
        (85.0, 5.0, 84.9, 85.1, "2026-04-15T12:02:00", None, 0.2, 0.2350, 4),
        (86.0, 5.0, 85.9, 86.1, "2026-04-15T12:03:00", "UNKNOWN", 0.2, 0.2323, 5),
    ]
    pd.DataFrame(
        rows,
        columns=[
            "price",
            "size",
            "bid",
            "ask",
            "time",
            "product_id",
            "spread",
            "spread_pct",
            "trade_id",
        ],
    ).to_sql("prices", conn, index=False, if_exists="replace")
    conn.commit()
    conn.close()


def test_cleanup_database_dry_run_and_execute(tmp_path):
    """Cleanup utility should report candidates and delete them when executed."""
    db_path = tmp_path / "cleanup.db"
    seed_prices_table(db_path)

    dry_run = cleanup_database(db_path=str(db_path), dry_run=True)
    assert dry_run["null_or_blank_candidates"] == 1
    assert dry_run["unknown_candidates"] == 1
    assert dry_run["duplicate_row_candidates"] == 1
    assert dry_run["total_rows_before"] == 5
    assert dry_run["total_rows_after"] == 5

    executed = cleanup_database(db_path=str(db_path), dry_run=False)
    assert executed["deleted_null_or_blank"] == 1
    assert executed["deleted_unknown"] == 1
    assert executed["deleted_duplicates"] == 1
    assert executed["total_rows_after"] == 2

    summary = get_database_summary(db_path=str(db_path))
    assert summary["total_rows"] == 2
    assert summary["invalid_rows"] == 0


def test_dashboard_metrics_endpoint(monkeypatch):
    """Dashboard endpoint should expose recruiter-friendly JSON metrics."""
    monkeypatch.setattr(
        "dashboard_api.get_database_summary",
        lambda: {
            "total_rows": 12,
            "invalid_rows": 0,
            "tracked_products": 3,
            "latest_timestamp": "2026-04-15T12:00:00",
            "product_counts": [{"product_id": "BTC-USD", "row_count": 10, "latest_time": "2026-04-15T12:00:00"}],
        },
    )
    monkeypatch.setattr(
        "dashboard_api.get_price_statistics",
        lambda product_id: {
            "count": 10,
            "current_price": 70000.0,
            "mean_price": 69500.0,
            "min_price": 68000.0,
            "max_price": 70500.0,
            "volatility": 1.5,
            "price_change_pct": 2.0,
            "avg_spread": 0.01,
        },
    )

    client = TestClient(app)
    response = client.get("/dashboard/metrics", params=[("products", "BTC-USD"), ("products", "ETH-USD")])

    assert response.status_code == 200
    payload = response.json()
    assert payload["project"] == "coinbase-crypto-data-pipeline"
    assert payload["database"]["total_rows"] == 12
    assert len(payload["products"]) == 2
    assert payload["products"][0]["product_id"] == "BTC-USD"


def test_run_collector_mode_honors_max_runs():
    """Collector mode should loop the requested number of times and sum inserted rows."""
    with patch("main.fetch_and_store", side_effect=[2, 3, 1]) as mock_fetch, patch("main.time.sleep") as mock_sleep:
        total = pipeline_main.run_collector_mode(["BTC-USD"], interval_seconds=1, max_runs=3)

    assert total == 6
    assert mock_fetch.call_count == 3
    assert mock_sleep.call_count == 2


