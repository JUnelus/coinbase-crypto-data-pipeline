"""Data extraction module for Coinbase API.

Fetches real-time ticker data from Coinbase public API with retry logic,
error handling, and response validation.
"""

import requests
from typing import Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry as UrllibRetry

from config import settings
from exceptions import APIException, APIRateLimitException
from logger_config import get_logger


logger = get_logger(__name__)


def _create_session_with_retries() -> requests.Session:
    """Create a requests session with automatic retry logic.

    Returns:
        Configured requests.Session with retry strategy
    """
    session = requests.Session()

    retry_strategy = UrllibRetry(
        total=settings.API_RETRIES,
        backoff_factor=settings.API_RETRY_DELAY,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET"])
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def fetch_coinbase_ticker(product_id: str = "BTC-USD") -> Dict[str, Any]:
    """Fetch ticker data from Coinbase API.

    Retrieves real-time ticker information including price, bid, ask,
    and volume for the specified product.

    Args:
        product_id: Coinbase product ID (e.g., 'BTC-USD', 'ETH-USD')

    Returns:
        Dictionary containing ticker data from Coinbase API

    Raises:
        APIRateLimitException: If API rate limit is exceeded
        APIException: If API request fails for other reasons

    Example:
        >>> ticker = fetch_coinbase_ticker('BTC-USD')
        >>> print(ticker['price'])
    """
    url = f"{settings.COINBASE_API_BASE_URL}/products/{product_id}/ticker"

    response = None
    try:
        session = _create_session_with_retries()
        logger.debug(f"Fetching ticker for {product_id} from {url}")

        response = session.get(url, timeout=settings.API_TIMEOUT)

        # Handle rate limiting
        if response.status_code == 429:
            logger.error(f"Rate limited by Coinbase API for {product_id}")
            raise APIRateLimitException(
                f"Rate limited. Retry after {response.headers.get('Retry-After', 'unknown')} seconds"
            )

        response.raise_for_status()
        data = response.json()

        logger.info(f"Successfully fetched ticker for {product_id}")
        logger.debug(f"Response: {data}")

        return data

    except APIRateLimitException:
        raise
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout fetching {product_id}: {str(e)}")
        raise APIException(f"API request timeout for {product_id}") from e
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error fetching {product_id}: {str(e)}")
        raise APIException(f"Connection error for {product_id}") from e
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error fetching {product_id}: {str(e)}")
        status_code = response.status_code if response is not None else "unknown"
        raise APIException(f"HTTP error for {product_id}: {status_code}") from e
    except Exception as e:
        logger.error(f"Unexpected error fetching {product_id}: {str(e)}")
        raise APIException(f"Unexpected error fetching {product_id}") from e


__all__ = ["fetch_coinbase_ticker"]
