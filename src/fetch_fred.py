"""
Fetch FRED series data via fredapi.

Fetches: WMTSECL1, WSEFINTL1, SWPT, DTWEXBGS
Saves raw CSVs to data/raw/{series_id}.csv
"""

import sys
from pathlib import Path

import pandas as pd
from fredapi import Fred

# Add project root to path for config import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import FRED_API_KEY, FRED_SERIES


def fetch_all_fred():
    """Fetch all configured FRED series. Skips failures gracefully."""
    if FRED_API_KEY == 'YOUR_KEY_HERE':
        print("  WARNING: FRED_API_KEY not set. Skipping FRED fetch.")
        print("  Set your key in .env or config.py")
        return

    fred = Fred(api_key=FRED_API_KEY)
    output_dir = Path('data/raw')
    output_dir.mkdir(parents=True, exist_ok=True)

    for series_id, description in FRED_SERIES.items():
        print(f"  Fetching {series_id} ({description})...")
        try:
            # Validate series exists
            info = fred.get_series_info(series_id)
            print(f"    Series confirmed: {info['title']}")

            # Fetch full history
            data = fred.get_series(series_id)

            # Convert to DataFrame with date,value columns
            df = pd.DataFrame({'date': data.index, 'value': data.values})
            df['date'] = pd.to_datetime(df['date'])

            # Replace any string '.' with NaN (FRED convention for missing)
            df['value'] = pd.to_numeric(df['value'], errors='coerce')

            # Drop rows where value is NaN
            df = df.dropna(subset=['value'])

            # Save
            outpath = output_dir / f"{series_id}.csv"
            df.to_csv(outpath, index=False)
            print(f"    Saved {len(df)} observations to {outpath}")

        except Exception as e:
            print(f"    ERROR fetching {series_id}: {e}")
            print(f"    Skipping — dashboard will show 'Data unavailable' for this series.")


if __name__ == '__main__':
    fetch_all_fred()
