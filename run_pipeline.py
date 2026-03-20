"""
Dollar Dominance Dashboard — Master Pipeline

Usage:
    python run_pipeline.py                       # Full pipeline: fetch + process + build
    python run_pipeline.py --no-fetch            # Rebuild dashboard from cached data
    python run_pipeline.py --fetch-only          # Fetch data without building dashboard
    python run_pipeline.py --validate            # Full pipeline + data validation
    python run_pipeline.py --validate-only       # Validate existing data (no fetch/build)
    python run_pipeline.py --validate --fix      # Full pipeline + validate + auto-fix
    python run_pipeline.py --validate-only --fix # Validate + auto-fix (no initial pipeline)
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
    parser.add_argument('--validate', action='store_true',
                        help='Run data validation after pipeline completes')
    parser.add_argument('--validate-only', action='store_true',
                        help='Run validation without rebuilding')
    parser.add_argument('--fix', action='store_true',
                        help='Auto-fix stale data (requires --validate or --validate-only)')
    args = parser.parse_args()

    # --fix requires a validation mode
    if args.fix and not (args.validate or args.validate_only):
        parser.error('--fix requires --validate or --validate-only')

    # Validate-only: skip everything, just run checks
    if args.validate_only:
        if args.fix:
            from src.validate_data import run_validation_with_fix
            success, fixes = run_validation_with_fix()
            if fixes:
                print(f"  Fixes applied: {', '.join(fixes)}")
        else:
            from src.validate_data import run_validation
            success = run_validation()
        sys.exit(0 if success else 1)

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

    # Post-pipeline validation
    if args.validate:
        if args.fix:
            from src.validate_data import run_validation_with_fix
            success, fixes = run_validation_with_fix()
            if fixes:
                print(f"  Fixes applied: {', '.join(fixes)}")
            if not success:
                sys.exit(1)
        else:
            from src.validate_data import run_validation
            run_validation()


if __name__ == '__main__':
    main()
