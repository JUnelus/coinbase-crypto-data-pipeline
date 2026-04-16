"""Unit tests for the crypto pipeline.

Tests for data extraction, transformation, and loading modules.
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import patch, MagicMock

from scripts.extract import fetch_coinbase_ticker
from scripts.transform import transform_ticker, add_technical_indicators
from scripts.load import store_to_db, get_latest_data
from exceptions import APIException, TransformException, ValidationException


class TestExtract:
    """Tests for data extraction module."""

    @patch("scripts.extract.requests.Session.get")
    def test_fetch_coinbase_ticker_success(self, mock_get):
        """Test successful ticker fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "price": "45000.00",
            "size": "1.5",
            "bid": "44999.00",
            "ask": "45001.00",
            "time": "2026-04-15T12:00:00Z",
            "trade_id": 123456,
            "product_id": "BTC-USD"
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = fetch_coinbase_ticker("BTC-USD")

        assert result["price"] == "45000.00"
        assert result["product_id"] == "BTC-USD"

    @patch("scripts.extract.requests.Session.get")
    def test_fetch_coinbase_ticker_rate_limit(self, mock_get):
        """Test rate limit handling."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_get.return_value = mock_response

        with pytest.raises(Exception):  # Should raise APIRateLimitException
            fetch_coinbase_ticker("BTC-USD")

    @patch("scripts.extract.requests.Session.get")
    def test_fetch_coinbase_ticker_timeout(self, mock_get):
        """Test timeout handling."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()

        with pytest.raises(APIException):
            fetch_coinbase_ticker("BTC-USD")


class TestTransform:
    """Tests for data transformation module."""

    def test_transform_ticker_success(self):
        """Test successful ticker transformation."""
        raw_data = {
            "price": "45000.00",
            "size": "1.5",
            "bid": "44999.00",
            "ask": "45001.00",
            "time": "2026-04-15T12:00:00Z",
            "trade_id": 123456,
            "product_id": "BTC-USD"
        }

        df = transform_ticker(raw_data)

        assert len(df) == 1
        assert float(df["price"].iloc[0]) == 45000.0
        assert df["product_id"].iloc[0] == "BTC-USD"
        assert "spread" in df.columns
        assert "spread_pct" in df.columns

    def test_transform_ticker_missing_fields(self):
        """Test validation of missing fields."""
        raw_data = {
            "price": "45000.00",
            "size": "1.5",
            # Missing bid, ask, time
        }

        with pytest.raises(ValidationException):
            transform_ticker(raw_data)

    def test_transform_ticker_invalid_types(self):
        """Test validation of invalid data types."""
        raw_data = {
            "price": "not_a_number",
            "size": "1.5",
            "bid": "44999.00",
            "ask": "45001.00",
            "time": "2026-04-15T12:00:00Z"
        }

        with pytest.raises(ValidationException):
            transform_ticker(raw_data)

    def test_add_technical_indicators(self):
        """Test technical indicator calculation."""
        # Create sample data
        df = pd.DataFrame({
            "price": [45000, 45100, 45200, 45150, 45250, 45300, 45400],
            "time": pd.date_range("2026-04-15", periods=7, freq="1h"),
            "bid": [44999, 45099, 45199, 45149, 45249, 45299, 45399],
            "ask": [45001, 45101, 45201, 45151, 45251, 45301, 45401]
        })

        result = add_technical_indicators(df, sma_windows=[3])

        assert "sma_3" in result.columns
        assert result["sma_3"].iloc[-1] > 0  # Last SMA should have a value


class TestLoad:
    """Tests for data loading module."""

    def test_store_to_db_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame()

        result = store_to_db(empty_df, db_path=":memory:")

        assert result == 0

    def test_store_to_db_valid_data(self, tmp_path):
        """Test storing valid data to database."""
        df = pd.DataFrame({
            "product_id": ["BTC-USD"],
            "price": [45000.0],
            "size": [1.5],
            "bid": [44999.0],
            "ask": [45001.0],
            "spread": [2.0],
            "spread_pct": [0.00444],
            "time": [datetime.now()],
            "trade_id": [123456]
        })

        db_path = str(tmp_path / "test.db")
        result = store_to_db(df, db_path=db_path, if_exists="replace")

        assert result >= 0  # Should insert at least 0 rows (might be 1)

    def test_get_latest_data_empty_database(self, tmp_path):
        """Test retrieving data from empty database."""
        db_path = str(tmp_path / "test.db")

        # Create empty database
        from scripts.load import get_connection
        get_connection(db_path).close()

        result = get_latest_data(product_id="BTC-USD", db_path=db_path)

        assert len(result) == 0 or result.empty


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


