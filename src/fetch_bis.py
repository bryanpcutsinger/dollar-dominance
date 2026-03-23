"""
Fetch BIS international debt securities data via SDMX REST API.

Queries the WS_DEBT_SEC2_PUB dataset for currency denomination shares
(TO1, USD, EU1) and saves to data/raw/bis_debt_raw.csv.
"""

import io
import sys
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# BIS SDMX REST API — public, no API key required
BIS_API_URL = (
    "https://stats.bis.org/api/v2/data/dataflow/BIS/WS_DEBT_SEC2_PUB/1.0/"
    "Q.3P.3P.1.1...A.TO1+USD+EU1.K.A.A...C"
    "?format=csv"
)


def fetch_bis_debt():
    """Fetch BIS international debt securities via SDMX API."""
    output_dir = Path('data/raw')
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_path = output_dir / 'bis_debt_raw.csv'

    print(f"  Querying BIS SDMX API...")

    try:
        r = requests.get(BIS_API_URL, timeout=60)
        r.raise_for_status()

        df = pd.read_csv(io.StringIO(r.text))
        print(f"  API returned {len(df)} rows")

        # Save raw API response
        df.to_csv(cache_path, index=False)
        print(f"  Saved to {cache_path}")

    except requests.RequestException as e:
        if cache_path.exists():
            print(f"  WARNING: BIS API request failed ({e}). Using cached data.")
        else:
            print(f"  ERROR: BIS API request failed and no cache available: {e}")


if __name__ == '__main__':
    fetch_bis_debt()
