"""Database cleanup utility for the crypto pipeline.

Usage examples:
    python -m scripts.cleanup_db --dry-run
    python -m scripts.cleanup_db --vacuum
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.load import cleanup_database, get_database_summary
from logger_config import setup_logging, get_logger


logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Clean legacy SQLite rows and report data quality metrics.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m scripts.cleanup_db --dry-run
  python -m scripts.cleanup_db --vacuum
  python -m scripts.cleanup_db --keep-unknown
        """,
    )
    parser.add_argument("--db-path", help="Optional path to an alternative SQLite DB file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview cleanup impact without deleting anything",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Show database summary only (alias of dry-run without cleanup actions)",
    )
    parser.add_argument(
        "--vacuum",
        action="store_true",
        help="Run VACUUM after cleanup to compact the database",
    )
    parser.add_argument(
        "--keep-unknown",
        action="store_true",
        help="Preserve rows where product_id='UNKNOWN'",
    )
    return parser


def main() -> int:
    """CLI entrypoint."""
    setup_logging()
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.report_only:
            summary = get_database_summary(db_path=args.db_path)
            print(json.dumps(summary, indent=2, default=str))
            return 0

        result = cleanup_database(
            db_path=args.db_path,
            dry_run=args.dry_run,
            remove_unknown=not args.keep_unknown,
            vacuum=args.vacuum,
        )
        print(json.dumps(result, indent=2, default=str))
        return 0

    except Exception as exc:
        logger.error(f"Cleanup utility failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

