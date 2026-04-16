"""Recruiter-facing FastAPI dashboard for crypto pipeline metrics.

Run locally with:
    uvicorn dashboard_api:app --reload
"""

from __future__ import annotations

from datetime import datetime, UTC
from importlib import import_module
from typing import Any

_fastapi = import_module("fastapi")
FastAPI = _fastapi.FastAPI
Query = _fastapi.Query

from config import settings
from scripts.load import get_database_summary
from scripts.visualize import get_price_statistics


app = FastAPI(
    title="Coinbase Crypto Pipeline Dashboard",
    description="Read-only recruiter/demo API for pipeline health and market metrics.",
    version="1.0.0",
)


def build_dashboard_payload(product_ids: list[str] | None = None) -> dict[str, Any]:
    """Build a concise JSON payload for recruiter demos."""
    selected_products = product_ids or settings.CRYPTO_PAIRS
    db_summary = get_database_summary()

    product_metrics = []
    for product_id in selected_products:
        stats = get_price_statistics(product_id)
        if stats:
            product_metrics.append(
                {
                    "product_id": product_id,
                    "count": int(stats["count"]),
                    "current_price": float(stats["current_price"]),
                    "mean_price": float(stats["mean_price"]),
                    "min_price": float(stats["min_price"]),
                    "max_price": float(stats["max_price"]),
                    "volatility": float(stats["volatility"]),
                    "price_change_pct": float(stats["price_change_pct"]),
                    "avg_spread": float(stats["avg_spread"]) if stats["avg_spread"] is not None else None,
                }
            )

    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "project": "coinbase-crypto-data-pipeline",
        "environment": settings.ENV,
        "configured_products": selected_products,
        "database": db_summary,
        "products": product_metrics,
    }


@app.get("/")
def root() -> dict[str, Any]:
    """Root endpoint for quick recruiter navigation."""
    return {
        "message": "Coinbase Crypto Data Pipeline recruiter dashboard",
        "endpoints": ["/health", "/dashboard/metrics"],
    }


@app.get("/health")
def health() -> dict[str, Any]:
    """Simple health endpoint for demos and uptime checks."""
    summary = get_database_summary()
    return {
        "status": "ok",
        "tracked_products": summary["tracked_products"],
        "total_rows": summary["total_rows"],
        "invalid_rows": summary["invalid_rows"],
        "latest_timestamp": summary["latest_timestamp"],
    }


@app.get("/dashboard/metrics")
def dashboard_metrics(products: list[str] | None = Query(default=None)) -> dict[str, Any]:
    """Return a recruiter-friendly JSON summary of pipeline health and asset metrics."""
    return build_dashboard_payload(products)


