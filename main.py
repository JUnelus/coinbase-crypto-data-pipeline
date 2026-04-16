"""Main entry point for the Coinbase crypto data pipeline.

Orchestrates the ETL process for fetching, transforming, and loading
cryptocurrency market data.

Usage:
    python main.py                      # Fetch default BTC-USD
    python main.py --products ETH-USD SOL-USD  # Fetch multiple products
"""

import argparse
import sys
import time
from typing import List, Optional

from scripts.extract import fetch_coinbase_ticker
from scripts.transform import transform_ticker, add_technical_indicators
import pandas as pd

from scripts.load import store_to_db, get_latest_data
from scripts.visualize import get_price_statistics, plot_price_history
from config import settings
from exceptions import PipelineException
from logger_config import get_logger, setup_logging


logger = get_logger(__name__)


def fetch_and_store(product_ids: List[str]) -> int:
    """Fetch data from Coinbase and store to database.

    Args:
        product_ids: List of Coinbase product IDs to fetch

    Returns:
        Total rows inserted
    """
    total_rows = 0

    for product_id in product_ids:
        try:
            logger.info(f"Processing {product_id}...")

            # Extract
            raw_data = fetch_coinbase_ticker(product_id)
            raw_data["product_id"] = product_id

            # Transform
            df = transform_ticker(raw_data)

            # Enrich latest row with rolling indicators from recent history.
            history = get_latest_data(product_id, limit=60)
            if not history.empty:
                history_for_calc = history[["price", "time"]].copy()
                combined = pd.concat([history_for_calc, df[["price", "time"]]], ignore_index=True)
            else:
                combined = df[["price", "time"]].copy()

            enriched = add_technical_indicators(combined, sma_windows=[20, 50], calculate_rsi=True)
            latest = enriched.iloc[-1]
            if "sma_20" in enriched.columns:
                df.loc[:, "sma_20"] = latest.get("sma_20")
            if "sma_50" in enriched.columns:
                df.loc[:, "sma_50"] = latest.get("sma_50")
            if "rsi_14" in enriched.columns:
                df.loc[:, "rsi_14"] = latest.get("rsi_14")

            # Store
            rows = store_to_db(df)
            total_rows += rows

            logger.info(f"[OK] {product_id}: {rows} rows inserted")

        except PipelineException as e:
            logger.error(f"[ERROR] {product_id}: {str(e)}")
            continue
        except Exception as e:
            logger.error(f"[ERROR] {product_id}: Unexpected error: {str(e)}")
            continue

    return total_rows


def run_collector_mode(
    product_ids: List[str],
    interval_seconds: int,
    max_runs: Optional[int] = None,
) -> int:
    """Continuously collect market data on a fixed interval.

    Args:
        product_ids: Products to collect each cycle.
        interval_seconds: Sleep interval between runs.
        max_runs: Optional number of cycles for demo/testing.

    Returns:
        Total rows inserted across all runs.
    """
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be greater than 0")

    total_rows = 0
    run_count = 0

    while max_runs is None or run_count < max_runs:
        run_count += 1
        logger.info(f"Collector cycle {run_count} started for: {', '.join(product_ids)}")
        inserted = fetch_and_store(product_ids)
        total_rows += inserted
        logger.info(f"Collector cycle {run_count} complete. Rows inserted this cycle: {inserted}")

        if max_runs is not None and run_count >= max_runs:
            break

        logger.info(f"Sleeping for {interval_seconds} seconds before next cycle")
        time.sleep(interval_seconds)

    return total_rows


def main():
    """Main pipeline orchestrator."""
    # Setup logging
    setup_logging()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Coinbase crypto data pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Fetch default BTC-USD
  python main.py --products ETH-USD # Fetch ETH-USD
  python main.py --stats BTC-USD    # Show statistics
        """
    )

    parser.add_argument(
        "--products",
        nargs="+",
        help="Coinbase product IDs to fetch (default: BTC-USD)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show price statistics for stored data"
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate visualization"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run collector in a scheduled loop for continuous demo ingestion"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=settings.FETCH_INTERVAL,
        help=f"Seconds between collector runs in --daemon mode (default: {settings.FETCH_INTERVAL})"
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        help="Optional number of collection cycles for demo/testing"
    )

    args = parser.parse_args()

    try:
        # Determine products to fetch
        products = args.products or settings.CRYPTO_PAIRS

        logger.info(f"Starting pipeline for: {', '.join(products)}")

        # Fetch and store data
        if args.daemon:
            total_rows = run_collector_mode(
                products,
                interval_seconds=args.interval,
                max_runs=args.max_runs,
            )
        else:
            total_rows = fetch_and_store(products)
        logger.info(f"Pipeline complete! Total rows inserted: {total_rows}")

        # Show statistics if requested
        if args.stats or not args.products:
            logger.info("\n=== Price Statistics ===")
            for product_id in products:
                try:
                    stats = get_price_statistics(product_id)
                    if stats:
                        logger.info(f"\n{product_id}:")
                        logger.info(f"  Current Price: ${stats['current_price']:.2f}")
                        logger.info(f"  Mean Price: ${stats['mean_price']:.2f}")
                        logger.info(f"  24h Range: ${stats['min_price']:.2f} - ${stats['max_price']:.2f}")
                        logger.info(f"  Volatility: {stats['volatility']:.2f}%")
                        if stats['price_change_pct'] > 0:
                            logger.info(f"  Change: +{stats['price_change_pct']:.2f}%")
                        else:
                            logger.info(f"  Change: {stats['price_change_pct']:.2f}%")
                except Exception as e:
                    logger.error(f"Failed to compute stats for {product_id}: {e}")

        # Generate plot if requested
        if args.plot:
            for product_id in products:
                try:
                    plot_path = f"data/{product_id.replace('-', '_')}_chart.png"
                    plot_price_history(product_id, save_path=plot_path)
                    logger.info(f"Saved chart to {plot_path}")
                except Exception as e:
                    logger.error(f"Failed to generate plot: {e}")

        return 0

    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
