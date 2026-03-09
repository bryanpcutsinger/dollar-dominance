"""
Process raw data into dashboard-ready CSVs.

Reads from data/raw/, writes to data/processed/.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RAW_DIR = Path('data/raw')
PROC_DIR = Path('data/processed')


def process_cofer():
    """Process COFER shares: convert quarterly dates, forward-fill gaps."""
    path = RAW_DIR / 'cofer_shares.csv'
    if not path.exists():
        print("  WARNING: cofer_shares.csv not found. Skipping COFER processing.")
        return None

    df = pd.read_csv(path, index_col=0)

    # Convert quarterly index (e.g., "1999-Q1") to datetime (end of quarter)
    df.index = pd.PeriodIndex(df.index, freq='Q').to_timestamp(how='end')
    df.index.name = 'date'

    # Forward-fill small gaps (max 2 quarters)
    df = df.ffill(limit=2)

    # Sort by date
    df = df.sort_index()

    outpath = PROC_DIR / 'cofer_shares.csv'
    df.to_csv(outpath)
    print(f"  COFER: {len(df)} quarters, {df.index[0].date()} to {df.index[-1].date()}")
    return df


def process_dxy():
    """Resample daily DXY to weekly (Friday close)."""
    path = RAW_DIR / 'DTWEXBGS.csv'
    if not path.exists():
        print("  WARNING: DTWEXBGS.csv not found. Skipping DXY.")
        return None

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')
    df.columns = ['dxy']

    # Resample to weekly — last value of each week ending Friday
    weekly = df.resample('W-FRI').last().dropna()

    outpath = PROC_DIR / 'dxy_weekly.csv'
    weekly.to_csv(outpath)
    print(f"  DXY: {len(weekly)} weekly observations")
    return weekly


def process_fx_turnover():
    """Create FX turnover CSV from hard-coded BIS Triennial data."""
    fx_turnover = {
        "year": [1992, 1995, 1998, 2001, 2004, 2007, 2010, 2013, 2016, 2019, 2022, 2025],
        "usd":  [82.0, 83.3, 87.3, 90.3, 88.7, 86.3, 84.9, 87.0, 87.6, 88.3, 88.4, 89.2],
        "eur":  [None, None, None, 37.6, 37.2, 37.0, 39.1, 33.4, 31.4, 32.3, 30.5, 28.9],
        "jpy":  [23.4, 24.1, 20.2, 22.7, 20.2, 16.5, 19.0, 23.1, 21.6, 16.8, 16.7, 16.8],
        "gbp":  [13.6, 9.4,  11.0, 13.2, 16.9, 14.8, 12.9, 11.8, 12.8, 12.8, 12.9, 10.2],
        "cny":  [None, None, None, 0.0,  0.1,  0.5,  0.9,  2.2,  4.0,  4.3,  7.0,  8.5],
    }
    df = pd.DataFrame(fx_turnover)

    outpath = PROC_DIR / 'fx_turnover_triennial.csv'
    df.to_csv(outpath, index=False)
    print(f"  FX turnover: {len(df)} survey years")
    return df


def process_bis_debt():
    """Process BIS bulk CSV into currency denomination shares."""
    path = RAW_DIR / 'bis_debt_raw.csv'
    if not path.exists():
        print("  WARNING: bis_debt_raw.csv not found. Skipping BIS debt securities.")
        return None

    print("  Processing BIS debt securities...")
    df = pd.read_csv(path, low_memory=False)

    # Filter: All countries excluding residents, all nationalities,
    # all issuers (immediate + ultimate), total maturities, all rates,
    # amounts outstanding, all currency groups
    mask = (
        (df['ISSUER_RES'] == '3P') &
        (df['ISSUER_NAT'] == '3P') &
        (df['ISSUER_BUS_IMM'] == '1') &
        (df['ISSUER_BUS_ULT'] == '1') &
        (df['ISSUE_OR_MAT'] == 'K') &
        (df['ISSUE_RE_MAT'] == 'A') &
        (df['ISSUE_RATE'] == 'A') &
        (df['MEASURE'] == 'C') &
        (df['ISSUE_CUR_GROUP'] == 'A')
    )
    filtered = df[mask]

    # Get time columns (quarterly dates like "2020-Q1")
    time_cols = [c for c in df.columns if c.startswith('19') or c.startswith('20')]

    # Extract rows for TO1 (total), USD, EU1 (Euro zone)
    currency_data = {}
    for cur in ['TO1', 'USD', 'EU1']:
        cur_rows = filtered[filtered['ISSUE_CUR'] == cur]
        if len(cur_rows) == 1:
            vals = cur_rows[time_cols].iloc[0].astype(float)
            currency_data[cur] = vals
        else:
            print(f"  WARNING: Expected 1 row for {cur}, got {len(cur_rows)}")

    if 'TO1' not in currency_data or 'USD' not in currency_data:
        print("  ERROR: Missing TO1 or USD data. Cannot compute shares.")
        return None

    # Build shares DataFrame
    total = currency_data['TO1']
    shares = pd.DataFrame(index=total.index)
    shares['usd'] = (currency_data.get('USD', 0) / total * 100)
    shares['eur'] = (currency_data.get('EU1', 0) / total * 100)
    shares['other'] = 100.0 - shares['usd'] - shares['eur']

    # Drop rows where total is 0 or NaN
    shares = shares[total > 0].dropna()

    # Convert index to proper quarterly dates
    shares.index = pd.PeriodIndex(shares.index, freq='Q').to_timestamp(how='end')
    shares.index.name = 'date'
    shares = shares.sort_index()

    # Filter to reasonable date range (data before ~2000 is spotty)
    shares = shares[shares.index >= '2000-01-01']

    outpath = PROC_DIR / 'debt_securities_shares.csv'
    shares.to_csv(outpath)
    print(f"  BIS debt: {len(shares)} quarters, {shares.index[0].date()} to {shares.index[-1].date()}")
    print(f"  Latest shares — USD: {shares['usd'].iloc[-1]:.1f}%, EUR: {shares['eur'].iloc[-1]:.1f}%, Other: {shares['other'].iloc[-1]:.1f}%")
    return shares


def build_metadata(cofer=None, dxy=None, debt=None, fx=None):
    """Create metadata.json with last-observation dates."""
    metadata = {
        "last_updated": datetime.now().isoformat(timespec='seconds'),
        "sources": {}
    }

    if cofer is not None and len(cofer) > 0:
        metadata["sources"]["cofer"] = {
            "last_obs": str(cofer.index[-1].date()),
            "source": "IMF COFER via SDMX API"
        }

    if fx is not None and len(fx) > 0:
        metadata["sources"]["fx_turnover"] = {
            "last_obs": f"April {int(fx['year'].iloc[-1])}",
            "source": "BIS Triennial Survey"
        }

    if debt is not None and len(debt) > 0:
        metadata["sources"]["debt_securities"] = {
            "last_obs": str(debt.index[-1].date()),
            "source": "BIS"
        }

    if dxy is not None and len(dxy) > 0:
        metadata["sources"]["dxy"] = {
            "last_obs": str(dxy.index[-1].date()),
            "source": "FRED DTWEXBGS"
        }

    outpath = PROC_DIR / 'metadata.json'
    with open(outpath, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"  Metadata saved to {outpath}")
    return metadata


def process_all():
    """Run all processing steps."""
    PROC_DIR.mkdir(parents=True, exist_ok=True)

    cofer = process_cofer()
    dxy = process_dxy()
    fx = process_fx_turnover()
    debt = process_bis_debt()

    build_metadata(cofer=cofer, dxy=dxy, debt=debt, fx=fx)


if __name__ == '__main__':
    process_all()
