"""
Fetch BIS international debt securities data via bulk CSV download.

Downloads the WS_DEBT_SEC2_PUB dataset, filters for currency denomination
shares, and saves to data/raw/bis_debt_raw.csv.

The BIS SDMX REST API is not publicly accessible — bulk CSV is the sole method.
"""

import io
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import BIS_BULK_DEBT_URL


def fetch_bis_debt():
    """Download and extract BIS international debt securities bulk CSV."""
    output_dir = Path('data/raw')
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_path = output_dir / 'bis_debt_raw.csv'

    print(f"  Downloading BIS bulk CSV (~40MB)...")
    print(f"  URL: {BIS_BULK_DEBT_URL}")

    try:
        r = requests.get(BIS_BULK_DEBT_URL, timeout=120)
        r.raise_for_status()

        # Extract CSV from zip
        z = zipfile.ZipFile(io.BytesIO(r.content))
        csv_files = z.namelist()
        print(f"  Zip contains: {csv_files}")

        # Use the first CSV file
        csv_filename = csv_files[0]
        print(f"  Extracting {csv_filename}...")

        df = pd.read_csv(z.open(csv_filename), low_memory=False)
        print(f"  Raw data: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"  Columns: {list(df.columns[:15])}...")

        # Save the full raw CSV for inspection/debugging
        df.to_csv(cache_path, index=False)
        print(f"  Saved raw BIS data to {cache_path}")

        # Print summary of available dimensions to help with filtering
        _inspect_bis_data(df)

    except requests.RequestException as e:
        if cache_path.exists():
            print(f"  WARNING: BIS download failed ({e}). Using cached data.")
        else:
            print(f"  ERROR: BIS download failed and no cache available: {e}")

    except Exception as e:
        print(f"  ERROR processing BIS data: {e}")


def _inspect_bis_data(df):
    """Print summary of BIS dataset dimensions for debugging."""
    print(f"\n  --- BIS Data Inspection ---")
    # Show unique values for key categorical columns
    for col in df.columns:
        if df[col].dtype == 'object' and df[col].nunique() < 30:
            print(f"  {col}: {df[col].nunique()} unique values")
            if df[col].nunique() <= 10:
                print(f"    Values: {sorted(df[col].unique())}")


if __name__ == '__main__':
    fetch_bis_debt()
