"""Data loading module for SQLite database.

Handles database connections, schema management, and data persistence
with proper error handling and optimization.
"""

from typing import Optional, Literal, Any
import sqlite3
from pathlib import Path
import pandas as pd

from config import DB_FILE
from exceptions import DatabaseException, LoadException
from logger_config import get_logger


logger = get_logger(__name__)


def _create_schema(conn: sqlite3.Connection) -> None:
    """Create database schema with optimized table structure.

    Args:
        conn: SQLite database connection

    Raises:
        DatabaseException: If schema creation fails
    """
    try:
        cursor = conn.cursor()

        # Create prices table with primary key and indexes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                price REAL NOT NULL,
                size REAL NOT NULL,
                bid REAL NOT NULL,
                ask REAL NOT NULL,
                spread REAL,
                spread_pct REAL,
                time TIMESTAMP NOT NULL,
                trade_id INTEGER,
                sma_20 REAL,
                sma_50 REAL,
                rsi_14 REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        logger.info("Database schema created successfully")

    except sqlite3.Error as e:
        logger.error(f"Schema creation failed: {str(e)}")
        raise DatabaseException(f"Failed to create schema: {str(e)}") from e


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def _get_existing_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def _ensure_columns(conn: sqlite3.Connection, table_name: str, df: pd.DataFrame) -> None:
    """Add missing columns to support schema evolution."""
    if not _table_exists(conn, table_name):
        return

    existing_columns = _get_existing_columns(conn, table_name)
    dtype_map = {
        "price": "REAL",
        "size": "REAL",
        "bid": "REAL",
        "ask": "REAL",
        "spread": "REAL",
        "spread_pct": "REAL",
        "time": "TIMESTAMP",
        "product_id": "TEXT",
        "trade_id": "INTEGER",
        "sma_20": "REAL",
        "sma_50": "REAL",
        "rsi_14": "REAL",
        "created_at": "TIMESTAMP",
    }

    for col in df.columns:
        if col not in existing_columns:
            sql_type = dtype_map.get(col, "TEXT")
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {col} {sql_type}")


def _expected_schema_frame() -> pd.DataFrame:
    """Return empty DataFrame with expected prices schema columns."""
    return pd.DataFrame(
        columns=[
            "product_id", "price", "size", "bid", "ask", "spread", "spread_pct",
            "time", "trade_id", "sma_20", "sma_50", "rsi_14", "created_at"
        ]
    )


def _ensure_indexes(conn: sqlite3.Connection, table_name: str = "prices") -> None:
    """Create indexes only when required columns are present."""
    if not _table_exists(conn, table_name):
        return

    existing_columns = _get_existing_columns(conn, table_name)

    if "time" in existing_columns:
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_time
            ON prices(time DESC)
        """)

    if "product_id" in existing_columns:
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_product_id
            ON prices(product_id)
        """)

    if {"product_id", "time"}.issubset(existing_columns):
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_product_time
            ON prices(product_id, time DESC)
        """)
        try:
            conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_product_time
                ON prices(product_id, time)
            """)
        except sqlite3.IntegrityError:
            logger.warning(
                "Skipped unique index creation because duplicate (product_id, time) rows still exist"
            )

    conn.commit()


def _migrate_legacy_time_unique_schema(conn: sqlite3.Connection) -> None:
    """Migrate legacy schema that had UNIQUE(time) to composite uniqueness."""
    if not _table_exists(conn, "prices"):
        return

    cursor = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='prices'"
    )
    row = cursor.fetchone()
    table_sql = (row[0] or "") if row else ""

    if "time TIMESTAMP NOT NULL UNIQUE" not in table_sql:
        return

    logger.info("Migrating legacy prices schema to composite unique key")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS prices_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            price REAL NOT NULL,
            size REAL NOT NULL,
            bid REAL NOT NULL,
            ask REAL NOT NULL,
            spread REAL,
            spread_pct REAL,
            time TIMESTAMP NOT NULL,
            trade_id INTEGER,
            sma_20 REAL,
            sma_50 REAL,
            rsi_14 REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    existing_columns = _get_existing_columns(conn, "prices")
    target_columns = [
        "product_id", "price", "size", "bid", "ask", "spread", "spread_pct",
        "time", "trade_id", "sma_20", "sma_50", "rsi_14", "created_at"
    ]

    select_exprs = []
    for col in target_columns:
        if col in existing_columns:
            select_exprs.append(col)
        elif col == "product_id":
            select_exprs.append("'BTC-USD' AS product_id")
        else:
            select_exprs.append(f"NULL AS {col}")

    conn.execute(
        "INSERT OR IGNORE INTO prices_new (product_id, price, size, bid, ask, spread, spread_pct, time, trade_id, sma_20, sma_50, rsi_14, created_at) "
        f"SELECT {', '.join(select_exprs)} FROM prices"
    )
    conn.execute("DROP TABLE prices")
    conn.execute("ALTER TABLE prices_new RENAME TO prices")
    conn.commit()


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Get a SQLite database connection.

    Args:
        db_path: Path to database file (default: config.DB_FILE)

    Returns:
        SQLite connection object

    Raises:
        DatabaseException: If connection fails
    """
    try:
        db_file = db_path or DB_FILE

        # Ensure directory exists
        Path(db_file).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_file))
        conn.row_factory = sqlite3.Row

        logger.debug(f"Connected to database: {db_file}")
        return conn

    except sqlite3.Error as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise DatabaseException(f"Failed to connect to database: {str(e)}") from e


def store_to_db(
    df: pd.DataFrame,
    db_path: Optional[str] = None,
    if_exists: Literal["fail", "replace", "append", "delete_rows"] = "append"
) -> int:
    """Store DataFrame to SQLite database.

    Persists ticker data to database with schema creation, conflict
    handling, and error reporting.

    Args:
        df: DataFrame with ticker data to store
        db_path: Path to database file (default: config.DB_FILE)
        if_exists: How to behave if table exists:
                  'fail': Raise error (default)
                  'replace': Drop table and create new
                  'append': Insert new rows

    Returns:
        Number of rows inserted

    Raises:
        LoadException: If loading fails

    Example:
        >>> df = transform_ticker(raw)
        >>> rows = store_to_db(df)
        >>> print(f"Inserted {rows} rows")
    """
    if df.empty:
        logger.warning("Attempted to store empty DataFrame")
        return 0

    try:
        db_file = db_path or DB_FILE

        with get_connection(db_file) as conn:
            _migrate_legacy_time_unique_schema(conn)
            # Create schema if needed
            _create_schema(conn)
            _ensure_columns(conn, "prices", df)
            _ensure_indexes(conn, "prices")

            # Store data
            initial_count = pd.read_sql(
                "SELECT COUNT(*) as count FROM prices",
                conn
            )["count"].iloc[0]

            df.to_sql("prices", conn, if_exists=if_exists, index=False)

            final_count = pd.read_sql(
                "SELECT COUNT(*) as count FROM prices",
                conn
            )["count"].iloc[0]

            rows_inserted = final_count - initial_count
            logger.info(f"Successfully stored {rows_inserted} rows to database")

            return rows_inserted

    except pd.errors.DatabaseError as e:
        logger.error(f"Pandas database error: {str(e)}")
        raise LoadException(f"Database write failed: {str(e)}") from e
    except sqlite3.IntegrityError as e:
        logger.warning(f"Integrity error (likely duplicate): {str(e)}")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error during store: {str(e)}")
        raise LoadException(f"Failed to store data: {str(e)}") from e


def get_latest_data(
    product_id: str = "BTC-USD",
    limit: int = 100,
    db_path: Optional[str] = None
) -> pd.DataFrame:
    """Retrieve latest ticker data from database.

    Args:
        product_id: Product ID to filter by
        limit: Maximum number of rows to return
        db_path: Path to database file

    Returns:
        DataFrame with latest ticker data
    """
    try:
        with get_connection(db_path or DB_FILE) as conn:
            _migrate_legacy_time_unique_schema(conn)
            _create_schema(conn)
            _ensure_columns(conn, "prices", _expected_schema_frame())
            _ensure_indexes(conn, "prices")

            query = """
                SELECT * FROM prices
                WHERE product_id = ?
                ORDER BY time DESC
                LIMIT ?
            """
            df = pd.read_sql(query, conn, params=(product_id, limit))
            df["time"] = pd.to_datetime(df["time"])

            logger.debug(f"Retrieved {len(df)} rows for {product_id}")
            return df.sort_values("time")

    except Exception as e:
        if "no such table" in str(e).lower():
            return pd.DataFrame()
        logger.error(f"Failed to retrieve data: {str(e)}")
        raise DatabaseException(f"Data retrieval failed: {str(e)}") from e


def get_database_summary(db_path: Optional[str] = None) -> dict[str, Any]:
    """Return a lightweight summary of stored data for dashboards and reporting."""
    try:
        with get_connection(db_path or DB_FILE) as conn:
            _migrate_legacy_time_unique_schema(conn)
            _create_schema(conn)
            _ensure_columns(conn, "prices", _expected_schema_frame())
            _ensure_indexes(conn, "prices")

            total_rows = int(conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0])
            invalid_rows = int(
                conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM prices
                    WHERE product_id IS NULL
                       OR TRIM(COALESCE(product_id, '')) = ''
                       OR product_id = 'UNKNOWN'
                    """
                ).fetchone()[0]
            )

            latest_timestamp = conn.execute(
                "SELECT MAX(time) FROM prices"
            ).fetchone()[0]

            product_counts_raw = conn.execute(
                """
                SELECT
                    CASE
                        WHEN product_id IS NULL OR TRIM(COALESCE(product_id, '')) = '' THEN 'UNLABELED'
                        ELSE product_id
                    END AS product_id,
                    COUNT(*) AS row_count,
                    MAX(time) AS latest_time
                FROM prices
                GROUP BY 1
                ORDER BY product_id
                """
            ).fetchall()

            product_counts = [
                {
                    "product_id": row[0],
                    "row_count": int(row[1]),
                    "latest_time": row[2],
                }
                for row in product_counts_raw
            ]

            return {
                "total_rows": total_rows,
                "invalid_rows": invalid_rows,
                "tracked_products": len(
                    [p for p in product_counts if p["product_id"] not in {"UNLABELED", "UNKNOWN"}]
                ),
                "latest_timestamp": latest_timestamp,
                "product_counts": product_counts,
            }

    except Exception as e:
        logger.error(f"Failed to summarize database: {str(e)}")
        raise DatabaseException(f"Failed to summarize database: {str(e)}") from e


def cleanup_database(
    db_path: Optional[str] = None,
    dry_run: bool = False,
    remove_unknown: bool = True,
    vacuum: bool = False,
) -> dict[str, Any]:
    """Clean legacy rows and duplicate records from the prices table.

    Removes rows with missing product labels and de-duplicates by
    `(product_id, time)` while keeping the earliest row.
    """
    try:
        with get_connection(db_path or DB_FILE) as conn:
            _migrate_legacy_time_unique_schema(conn)
            _create_schema(conn)
            _ensure_columns(conn, "prices", _expected_schema_frame())
            _ensure_indexes(conn, "prices")

            total_before = int(conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0])
            null_or_blank_count = int(
                conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM prices
                    WHERE product_id IS NULL OR TRIM(COALESCE(product_id, '')) = ''
                    """
                ).fetchone()[0]
            )
            unknown_count = int(
                conn.execute(
                    "SELECT COUNT(*) FROM prices WHERE product_id = 'UNKNOWN'"
                ).fetchone()[0]
            )
            duplicate_groups = int(
                conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM (
                        SELECT COALESCE(NULLIF(TRIM(product_id), ''), 'UNKNOWN') AS product_key, time
                        FROM prices
                        GROUP BY product_key, time
                        HAVING COUNT(*) > 1
                    )
                    """
                ).fetchone()[0]
            )
            duplicate_rows = int(
                conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM prices
                    WHERE rowid NOT IN (
                        SELECT MIN(rowid)
                        FROM prices
                        GROUP BY COALESCE(NULLIF(TRIM(product_id), ''), 'UNKNOWN'), time
                    )
                    """
                ).fetchone()[0]
            )

            deleted_null_or_blank = 0
            deleted_unknown = 0
            deleted_duplicates = 0

            if not dry_run:
                deleted_null_or_blank = conn.execute(
                    "DELETE FROM prices WHERE product_id IS NULL OR TRIM(COALESCE(product_id, '')) = ''"
                ).rowcount

                if remove_unknown:
                    deleted_unknown = conn.execute(
                        "DELETE FROM prices WHERE product_id = 'UNKNOWN'"
                    ).rowcount

                deleted_duplicates = conn.execute(
                    """
                    DELETE FROM prices
                    WHERE rowid NOT IN (
                        SELECT MIN(rowid)
                        FROM prices
                        GROUP BY COALESCE(NULLIF(TRIM(product_id), ''), 'UNKNOWN'), time
                    )
                    """
                ).rowcount

                conn.commit()

                if vacuum:
                    conn.execute("VACUUM")

                _ensure_indexes(conn, "prices")

            total_after = int(conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0])

            return {
                "dry_run": dry_run,
                "total_rows_before": total_before,
                "total_rows_after": total_after,
                "null_or_blank_candidates": null_or_blank_count,
                "unknown_candidates": unknown_count,
                "duplicate_groups": duplicate_groups,
                "duplicate_row_candidates": duplicate_rows,
                "deleted_null_or_blank": int(deleted_null_or_blank),
                "deleted_unknown": int(deleted_unknown),
                "deleted_duplicates": int(deleted_duplicates),
                "vacuumed": bool(vacuum and not dry_run),
            }

    except Exception as e:
        logger.error(f"Failed to clean database: {str(e)}")
        raise DatabaseException(f"Failed to clean database: {str(e)}") from e


__all__ = [
    "store_to_db",
    "get_connection",
    "get_latest_data",
    "get_database_summary",
    "cleanup_database",
]
