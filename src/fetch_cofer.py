"""
Fetch IMF COFER data.

Primary source: IMF SDMX API (api.imf.org)
Fallback 1: DBnomics mirror of IMF COFER dataset
Fallback 2: cached data in data/raw/cofer_shares.csv

Saves raw data to data/raw/cofer_shares.csv
"""

import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DBNOMICS_BASE, COFER_DATASET

# --- IMF SDMX API (primary) ---

IMF_API_BASE = "https://api.imf.org/external/sdmx/2.1"

# COFER dimension key: COUNTRY.INDICATOR.FXR_CURRENCY.TYPE_OF_TRANSFORMATION.FREQUENCY
# G001 = World total (reporting countries)
# AFXRA = Allocated foreign exchange reserves
# SHRO_PT = Shares (percent)
# Q = Quarterly
IMF_COFER_KEY = "G001.AFXRA..SHRO_PT.Q"

# Map IMF currency codes to our column names
IMF_CURRENCY_MAP = {
    'CI_USD': 'usd', 'CI_EUR': 'eur', 'CI_CNY': 'cny', 'CI_JPY': 'jpy',
    'CI_GBP': 'gbp', 'CI_AUD': 'aud', 'CI_CAD': 'cad', 'CI_CHF': 'chf',
    'CI_OTHC': 'other',
}


def _fetch_imf_api(max_retries=3):
    """Fetch COFER data from the IMF SDMX 2.1 API.

    Returns a DataFrame with columns: usd, eur, cny, jpy, gbp, aud, cad, chf, other
    indexed by quarterly date strings (e.g. '1999-Q1'), or None on failure.
    """
    url = f"{IMF_API_BASE}/data/COFER/{IMF_COFER_KEY}"

    for attempt in range(max_retries):
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            break
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"    Retry {attempt + 1}/{max_retries} for IMF API (waiting {wait}s)...")
                time.sleep(wait)
            else:
                print(f"    ERROR: IMF API failed after {max_retries} attempts: {e}")
                return None

    # Parse SDMX XML — extract Series elements and their Obs children
    text = r.text
    series_re = r'<Series\s+([^>]+)>(.*?)</Series>'
    obs_re = r'<Obs\s+([^/]+)/>'

    currency_data = {}
    for sm in re.finditer(series_re, text, re.DOTALL):
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', sm.group(1)))
        imf_currency = attrs.get('FXR_CURRENCY', '')

        col_name = IMF_CURRENCY_MAP.get(imf_currency)
        if col_name is None:
            continue  # skip CI_T (total) and legacy codes

        obs_list = []
        for om in re.finditer(obs_re, sm.group(2)):
            oa = dict(re.findall(r'(\w+)="([^"]*)"', om.group(1)))
            period = oa.get('TIME_PERIOD', '')
            value = oa.get('OBS_VALUE', '')
            if period and value:
                obs_list.append((period, float(value)))

        currency_data[col_name] = obs_list

    if not currency_data:
        print("    WARNING: IMF API returned no parseable series")
        return None

    # Build DataFrame from all series
    all_dates = set()
    for obs_list in currency_data.values():
        for date, _ in obs_list:
            all_dates.add(date)

    dates = sorted(all_dates)
    df_data = {'date': dates}
    for col_name, obs_list in currency_data.items():
        date_val = {d: v for d, v in obs_list}
        df_data[col_name] = [date_val.get(d, None) for d in dates]

    df = pd.DataFrame(df_data).set_index('date')
    return df


# --- DBnomics fallback ---

COFER_CURRENCIES_DBNOMICS = {
    'usd': 'Q.W00.RAXGFXARUSDRT_PT',
    'eur': 'Q.W00.RAXGFXAREURORT_PT',
    'cny': 'Q.W00.RAXGFXARCNYRT_PT',
    'jpy': 'Q.W00.RAXGFXARJPYRT_PT',
    'gbp': 'Q.W00.RAXGFXARGBPRT_PT',
    'aud': 'Q.W00.RAXGFXARAUDRT_PT',
    'cad': 'Q.W00.RAXGFXARCADRT_PT',
    'chf': 'Q.W00.RAXGFXARCHFRT_PT',
    'other': 'Q.W00.RAXGFXAROCRT_PT',
}


def _fetch_dbnomics_series(series_code, max_retries=3):
    """Fetch a single COFER series from DBnomics with retries."""
    url = f"{DBNOMICS_BASE}/series/IMF/COFER/{series_code}?observations=1"

    for attempt in range(max_retries):
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()

            docs = data.get('series', {}).get('docs', [])
            if not docs:
                return None

            doc = docs[0]
            periods = doc.get('period', [])
            values = doc.get('value', [])

            if not periods or not values:
                return None

            return pd.Series(values, index=periods, name=series_code, dtype=float)

        except requests.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"    ERROR: DBnomics failed for {series_code}: {e}")
                return None


def _fetch_dbnomics_all():
    """Fetch all COFER series from DBnomics. Returns DataFrame or None."""
    all_series = {}
    for currency, code in COFER_CURRENCIES_DBNOMICS.items():
        print(f"    DBnomics: fetching {currency.upper()}...")
        s = _fetch_dbnomics_series(code)
        if s is not None:
            all_series[currency] = s
            time.sleep(0.5)

    if not all_series:
        return None

    df = pd.DataFrame(all_series)
    df.index.name = 'date'
    return df.sort_index()


# --- Main entry point ---

def fetch_cofer():
    """Fetch COFER data with 3-tier fallback: IMF API → DBnomics → cache."""
    output_dir = Path('data/raw')
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_path = output_dir / 'cofer_shares.csv'

    # Tier 1: IMF SDMX API
    print("  Trying IMF API (api.imf.org)...")
    df = _fetch_imf_api()
    if df is not None and len(df) > 0:
        source = "IMF API"
    else:
        # Tier 2: DBnomics
        print("  IMF API failed. Trying DBnomics fallback...")
        df = _fetch_dbnomics_all()
        if df is not None and len(df) > 0:
            source = "DBnomics"
        else:
            # Tier 3: cached data
            if cache_path.exists():
                print("  WARNING: All COFER fetches failed. Using cached data.")
                return
            else:
                print("  ERROR: All COFER fetches failed and no cache available.")
                return

    df = df.sort_index()
    df.to_csv(cache_path)

    n_currencies = df.notna().any().sum()
    print(f"  Saved COFER data ({source}): {len(df)} quarters, {n_currencies} currencies")
    print(f"  Date range: {df.index[0]} to {df.index[-1]}")


if __name__ == '__main__':
    fetch_cofer()
