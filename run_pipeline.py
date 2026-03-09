"""
Dollar Dominance Dashboard — Master Pipeline

Usage:
    python run_pipeline.py              # Full pipeline: fetch + process + build
    python run_pipeline.py --no-fetch   # Rebuild dashboard from cached data
    python run_pipeline.py --fetch-only # Fetch data without building dashboard
"""

import argparse
import shutil
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Dollar Dominance Dashboard Pipeline")
    parser.add_argument('--no-fetch', action='store_true',
                        help='Rebuild dashboard from cached CSVs (no network calls)')
    parser.add_argument('--fetch-only', action='store_true',
                        help='Fetch data without building dashboard')
    args = parser.parse_args()

    # Ensure directories exist
    Path('data/raw').mkdir(parents=True, exist_ok=True)
    Path('data/processed').mkdir(parents=True, exist_ok=True)
    Path('output').mkdir(parents=True, exist_ok=True)

    if not args.no_fetch:
        print("=== Fetching FRED data ===")
        from src.fetch_fred import fetch_all_fred
        fetch_all_fred()

        print("\n=== Fetching IMF COFER data ===")
        from src.fetch_cofer import fetch_cofer
        fetch_cofer()

        print("\n=== Fetching BIS debt securities data ===")
        from src.fetch_bis import fetch_bis_debt
        fetch_bis_debt()

    if args.fetch_only:
        print("\nFetch complete. Exiting.")
        sys.exit(0)

    print("\n=== Processing data ===")
    from src.process_data import process_all
    process_all()

    print("\n=== Building dashboard ===")
    from src.build_dashboard import build_dashboard
    build_dashboard()

    # Copy to docs/ for GitHub Pages
    docs_dir = Path('docs')
    docs_dir.mkdir(exist_ok=True)
    shutil.copy2('output/index.html', docs_dir / 'index.html')
    print(f"  Copied to {docs_dir / 'index.html'} (GitHub Pages)")

    print("\n=== Done. Dashboard at output/index.html ===")


if __name__ == '__main__':
    main()
