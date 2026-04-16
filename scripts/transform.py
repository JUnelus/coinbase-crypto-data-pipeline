"""Data transformation module for Coinbase ticker data.

Transforms raw API responses into clean DataFrames with technical indicators
and data quality checks.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

from exceptions import TransformException, ValidationException
from logger_config import get_logger


logger = get_logger(__name__)


def _validate_ticker_data(raw: Dict[str, Any]) -> None:
    """Validate required fields in raw ticker data.

    Args:
        raw: Raw ticker data from Coinbase API

    Raises:
        ValidationException: If required fields are missing or invalid
    """
    required_fields = ["price", "size", "bid", "ask", "time"]
    missing_fields = [f for f in required_fields if f not in raw]

    if missing_fields:
        raise ValidationException(
            f"Missing required fields: {missing_fields}"
        )

    try:
        float(raw["price"])
        float(raw["size"])
        float(raw["bid"])
        float(raw["ask"])
        pd.to_datetime(raw["time"])
    except (ValueError, TypeError) as e:
        raise ValidationException(f"Invalid data types: {str(e)}") from e


def _calculate_sma(prices: pd.Series, window: int) -> Optional[float]:
    """Calculate Simple Moving Average.

    Args:
        prices: Series of price values
        window: Window size for SMA calculation

    Returns:
        SMA value or None if insufficient data
    """
    if len(prices) < window:
        return None
    return prices.iloc[-window:].mean()


def _calculate_rsi(prices: pd.Series, period: int = 14) -> Optional[float]:
    """Calculate Relative Strength Index.

    Args:
        prices: Series of price values
        period: RSI period (default 14)

    Returns:
        RSI value or None if insufficient data
    """
    if len(prices) < period + 1:
        return None

    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])

    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def transform_ticker(raw: Dict[str, Any]) -> pd.DataFrame:
    """Transform raw ticker data into a clean DataFrame.

    Converts raw Coinbase API response into a structured DataFrame
    with normalized data types and quality validation.

    Args:
        raw: Raw ticker data from Coinbase API

    Returns:
        Transformed DataFrame with cleaned data

    Raises:
        TransformException: If transformation fails

    Example:
        >>> raw = fetch_coinbase_ticker('BTC-USD')
        >>> df = transform_ticker(raw)
        >>> print(df.columns)
    """
    try:
        # Validate raw data
        _validate_ticker_data(raw)

        # Extract and transform fields
        data = {
            "price": float(raw["price"]),
            "size": float(raw["size"]),
            "bid": float(raw["bid"]),
            "ask": float(raw["ask"]),
            "spread": float(raw["ask"]) - float(raw["bid"]),
            "spread_pct": ((float(raw["ask"]) - float(raw["bid"])) / float(raw["ask"])) * 100,
            "time": pd.to_datetime(raw["time"], utc=True).tz_localize(None),
            "product_id": raw.get("product_id", "UNKNOWN"),
            "trade_id": raw.get("trade_id"),
        }

        df = pd.DataFrame([data])

        # Ensure correct data types
        df = df.astype({
            "price": "float64",
            "size": "float64",
            "bid": "float64",
            "ask": "float64",
            "spread": "float64",
            "spread_pct": "float64",
        })

        logger.debug(f"Successfully transformed ticker data: {df.to_dict()}")
        return df

    except ValidationException as e:
        logger.error(f"Validation failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Transformation failed: {str(e)}")
        raise TransformException(f"Failed to transform ticker data: {str(e)}") from e


def add_technical_indicators(
    df: pd.DataFrame,
    sma_windows: Optional[list] = None,
    calculate_rsi: bool = True
) -> pd.DataFrame:
    """Add technical indicators to price DataFrame.

    Args:
        df: DataFrame with price data (must have 'price' column)
        sma_windows: List of window sizes for SMAs (default: [20, 50])
        calculate_rsi: Whether to calculate RSI (default: True)

    Returns:
        DataFrame with added technical indicator columns

    Raises:
        TransformException: If calculation fails
    """
    if sma_windows is None:
        sma_windows = [20, 50]

    try:
        df = df.copy()
        # Calculate SMAs
        for window in sma_windows:
            col_name = f"sma_{window}"
            df[col_name] = df["price"].rolling(window=window, min_periods=1).mean()

        # Calculate RSI
        if calculate_rsi and len(df) >= 15:
            rsi_values = []
            for i in range(len(df)):
                rsi = _calculate_rsi(df["price"].iloc[:i+1].values, period=14)
                rsi_values.append(rsi)
            df["rsi_14"] = rsi_values

        logger.debug(f"Added technical indicators to {len(df)} rows")
        return df

    except Exception as e:
        logger.error(f"Failed to add technical indicators: {str(e)}")
        raise TransformException(f"Technical indicator calculation failed: {str(e)}") from e


__all__ = ["transform_ticker", "add_technical_indicators"]
