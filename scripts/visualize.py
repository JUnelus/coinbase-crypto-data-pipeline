"""Visualization module for crypto price analysis.

Generates charts and plots for price history, technical indicators,
and portfolio metrics.
"""

from typing import Optional, List
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import pandas as pd

from scripts.load import get_latest_data
from logger_config import get_logger


logger = get_logger(__name__)


def plot_price_history(
    product_id: str = "BTC-USD",
    limit: int = 200,
    show_indicators: bool = True,
    save_path: Optional[str] = None
) -> Figure:
    """Plot price history with optional technical indicators.

    Args:
        product_id: Coinbase product ID
        limit: Number of data points to retrieve
        show_indicators: Whether to plot SMA and other indicators
        save_path: If provided, save plot to this file

    Returns:
        Matplotlib Figure object
    """
    try:
        df = get_latest_data(product_id, limit=limit)

        if df.empty:
            logger.warning(f"No data found for {product_id}")
            return None

        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))
        fig.suptitle(f"{product_id} Price Analysis", fontsize=16, fontweight="bold")

        # Plot prices with indicators
        ax1.plot(df["time"], df["price"], label="Price", linewidth=2, color="blue")

        if show_indicators:
            if "sma_20" in df.columns:
                ax1.plot(df["time"], df["sma_20"], label="SMA 20", alpha=0.7, color="orange")
            if "sma_50" in df.columns:
                ax1.plot(df["time"], df["sma_50"], label="SMA 50", alpha=0.7, color="red")

        ax1.set_ylabel("Price (USD)", fontweight="bold")
        ax1.legend(loc="best")
        ax1.grid(True, alpha=0.3)

        # Plot bid-ask spread
        ax2.fill_between(df["time"], df["bid"], df["ask"], alpha=0.3, label="Bid-Ask Spread")
        ax2.plot(df["time"], df["bid"], label="Bid", linewidth=1, alpha=0.7)
        ax2.plot(df["time"], df["ask"], label="Ask", linewidth=1, alpha=0.7)

        ax2.set_xlabel("Time", fontweight="bold")
        ax2.set_ylabel("Price (USD)", fontweight="bold")
        ax2.legend(loc="best")
        ax2.grid(True, alpha=0.3)

        # Format x-axis dates
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha="right")

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            logger.info(f"Plot saved to {save_path}")

        logger.info(f"Generated price history plot for {product_id}")
        return fig

    except Exception as e:
        logger.error(f"Failed to generate price plot: {str(e)}")
        raise


def plot_multi_product_comparison(
    product_ids: List[str],
    limit: int = 200,
    save_path: Optional[str] = None
) -> Figure:
    """Compare price movements across multiple products.

    Args:
        product_ids: List of Coinbase product IDs
        limit: Number of data points to retrieve
        save_path: If provided, save plot to this file

    Returns:
        Matplotlib Figure object
    """
    try:
        fig, ax = plt.subplots(figsize=(14, 8))

        for product_id in product_ids:
            df = get_latest_data(product_id, limit=limit)
            if not df.empty:
                # Normalize prices to percentage change for comparison
                df["price_normalized"] = (df["price"] / df["price"].iloc[0]) * 100
                ax.plot(df["time"], df["price_normalized"], label=product_id, linewidth=2)

        ax.set_xlabel("Time", fontweight="bold")
        ax.set_ylabel("Price Change (%)", fontweight="bold")
        ax.set_title("Multi-Product Price Comparison", fontsize=14, fontweight="bold")
        ax.legend(loc="best")
        ax.grid(True, alpha=0.3)

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            logger.info(f"Comparison plot saved to {save_path}")

        logger.info(f"Generated comparison plot for {product_ids}")
        return fig

    except Exception as e:
        logger.error(f"Failed to generate comparison plot: {str(e)}")
        raise


def get_price_statistics(
    product_id: str = "BTC-USD",
    limit: int = 500
) -> dict:
    """Calculate price statistics for analysis.

    Args:
        product_id: Coinbase product ID
        limit: Number of data points to use

    Returns:
        Dictionary with statistical metrics
    """
    try:
        df = get_latest_data(product_id, limit=limit)

        if df.empty:
            return {}

        price = df["price"]
        std_dev = float(price.std()) if len(price) > 1 else 0.0
        mean_price = float(price.mean())
        volatility = (std_dev / mean_price) * 100 if mean_price else 0.0

        stats = {
            "product_id": product_id,
            "count": len(df),
            "current_price": price.iloc[-1],
            "mean_price": mean_price,
            "median_price": price.median(),
            "min_price": price.min(),
            "max_price": price.max(),
            "std_dev": std_dev,
            "volatility": volatility,
            "price_change": price.iloc[-1] - price.iloc[0],
            "price_change_pct": ((price.iloc[-1] - price.iloc[0]) / price.iloc[0]) * 100,
            "avg_spread": df["spread_pct"].mean() if "spread_pct" in df.columns else None,
        }

        logger.info(f"Calculated statistics for {product_id}")
        return stats

    except Exception as e:
        logger.error(f"Failed to calculate statistics: {str(e)}")
        raise


if __name__ == "__main__":
    # Example usage
    plot_price_history("BTC-USD", save_path="data/btc_price_history.png")
    plt.show()

