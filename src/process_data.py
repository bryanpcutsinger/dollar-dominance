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
    """Process BIS SDMX API data into currency denomination shares."""
    path = RAW_DIR / 'bis_debt_raw.csv'
    if not path.exists():
        print("  WARNING: bis_debt_raw.csv not found. Skipping BIS debt securities.")
        return None

    print("  Processing BIS debt securities...")
    df = pd.read_csv(path, low_memory=False)

    # API returns long-format: each row is one observation with
    # ISSUE_CUR (TO1/USD/EU1), TIME_PERIOD (e.g. "2020-Q1"), OBS_VALUE
    pivot = df.pivot_table(
        index='TIME_PERIOD', columns='ISSUE_CUR',
        values='OBS_VALUE', aggfunc='first'
    )

    if 'TO1' not in pivot.columns or 'USD' not in pivot.columns:
        print("  ERROR: Missing TO1 or USD data. Cannot compute shares.")
        return None

    # Compute shares
    shares = pd.DataFrame(index=pivot.index)
    shares['usd'] = (pivot['USD'] / pivot['TO1'] * 100)
    shares['eur'] = (pivot.get('EU1', 0) / pivot['TO1'] * 100)
    shares['other'] = 100.0 - shares['usd'] - shares['eur']

    # Drop rows where total is 0 or NaN
    shares = shares[pivot['TO1'] > 0].dropna()

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


def process_treasuries():
    """Compute foreign share of publicly held US federal debt.

    Foreign share: FDHBFIN (billions) × 1000 / FYGFDPUN (millions) × 100.
    Output: treasury_foreign_share.csv with columns: date, foreign_share.
    """
    fdhbfin_path = RAW_DIR / 'FDHBFIN.csv'
    fygfdpun_path = RAW_DIR / 'FYGFDPUN.csv'

    if not fdhbfin_path.exists() or not fygfdpun_path.exists():
        print("  WARNING: FDHBFIN.csv or FYGFDPUN.csv not found. Skipping Treasury processing.")
        return None

    # Read foreign holdings (billions) and debt held by public (millions)
    foreign = pd.read_csv(fdhbfin_path, parse_dates=['date'], index_col='date')
    public = pd.read_csv(fygfdpun_path, parse_dates=['date'], index_col='date')

    foreign.columns = ['foreign_billions']
    public.columns = ['public_millions']

    # Convert to quarterly periods for alignment
    foreign['period'] = foreign.index.to_period('Q')
    public['period'] = public.index.to_period('Q')

    # Inner-join foreign + public debt
    merged = foreign.merge(public, on='period', how='inner')

    # Compute foreign share: FDHBFIN is billions, FYGFDPUN is millions
    merged['foreign_share'] = (merged['foreign_billions'] * 1000 / merged['public_millions']) * 100

    # Sanity check foreign share
    out_of_bounds = (merged['foreign_share'] < 1) | (merged['foreign_share'] > 70)
    if out_of_bounds.any():
        print(f"  WARNING: {out_of_bounds.sum()} foreign share values outside 1-70% range. Skipping.")
        return None

    result = pd.DataFrame({
        'date': merged['period'].dt.to_timestamp(how='end'),
        'foreign_share': merged['foreign_share'].values,
    })
    result = result.set_index('date').sort_index().dropna(subset=['foreign_share'])

    outpath = PROC_DIR / 'treasury_foreign_share.csv'
    result.to_csv(outpath)
    print(f"  Treasuries (foreign): {len(result)} quarters, {result.index[0].date()} to {result.index[-1].date()}")
    print(f"  Latest foreign share: {result['foreign_share'].iloc[-1]:.1f}%")
    return result


def process_fed_holdings():
    """Compute Fed share of publicly held US federal debt.

    Fed share: FDHBFRBN (billions) × 1000 / FYGFDPUN (millions) × 100.
    Output: treasury_fed_share.csv with columns: date, fed_share.
    """
    fdhbfrbn_path = RAW_DIR / 'FDHBFRBN.csv'
    fygfdpun_path = RAW_DIR / 'FYGFDPUN.csv'

    if not fdhbfrbn_path.exists() or not fygfdpun_path.exists():
        print("  WARNING: FDHBFRBN.csv or FYGFDPUN.csv not found. Skipping Fed holdings processing.")
        return None

    fed = pd.read_csv(fdhbfrbn_path, parse_dates=['date'], index_col='date')
    public = pd.read_csv(fygfdpun_path, parse_dates=['date'], index_col='date')

    fed.columns = ['fed_billions']
    public.columns = ['public_millions']

    # Convert to quarterly periods for alignment
    fed['period'] = fed.index.to_period('Q')
    public['period'] = public.index.to_period('Q')

    # Inner-join Fed + public debt (independent of foreign holdings)
    merged = fed.merge(public, on='period', how='inner')

    # Compute Fed share: FDHBFRBN is billions, FYGFDPUN is millions
    merged['fed_share'] = (merged['fed_billions'] * 1000 / merged['public_millions']) * 100

    # Sanity check
    out_of_bounds = (merged['fed_share'] < 1) | (merged['fed_share'] > 50)
    if out_of_bounds.any():
        print(f"  WARNING: {out_of_bounds.sum()} fed_share values outside 1-50% range.")

    result = pd.DataFrame({
        'date': merged['period'].dt.to_timestamp(how='end'),
        'fed_share': merged['fed_share'].values,
    })
    result = result.set_index('date').sort_index().dropna(subset=['fed_share'])

    outpath = PROC_DIR / 'treasury_fed_share.csv'
    result.to_csv(outpath)
    print(f"  Treasuries (Fed): {len(result)} quarters, {result.index[0].date()} to {result.index[-1].date()}")
    print(f"  Latest Fed share: {result['fed_share'].iloc[-1]:.1f}%")
    return result


def process_current_account():
    """Compute U.S. current account balance as percent of GDP.

    Uses NETFI (current account, billions SAAR) / GDP (billions SAAR) × 100.
    Output: current_account_gdp.csv with columns: date, ca_pct_gdp.
    """
    netfi_path = RAW_DIR / 'NETFI.csv'
    gdp_path = RAW_DIR / 'GDP.csv'

    if not netfi_path.exists() or not gdp_path.exists():
        print("  WARNING: NETFI.csv or GDP.csv not found. Skipping current account processing.")
        return None

    netfi = pd.read_csv(netfi_path, parse_dates=['date'], index_col='date')
    gdp = pd.read_csv(gdp_path, parse_dates=['date'], index_col='date')

    netfi.columns = ['netfi']
    gdp.columns = ['gdp']

    # Align on quarterly periods
    netfi['period'] = netfi.index.to_period('Q')
    gdp['period'] = gdp.index.to_period('Q')

    merged = netfi.merge(gdp, on='period', how='inner')
    merged['ca_pct_gdp'] = (merged['netfi'] / merged['gdp']) * 100

    # Sanity check: historical U.S. range roughly -8% to +5% (early post-war surpluses)
    out_of_bounds = (merged['ca_pct_gdp'] < -8) | (merged['ca_pct_gdp'] > 5)
    if out_of_bounds.any():
        print(f"  WARNING: {out_of_bounds.sum()} current account values outside -8% to +3% range.")

    result = pd.DataFrame({
        'date': merged['period'].dt.to_timestamp(how='end'),
        'ca_pct_gdp': merged['ca_pct_gdp'].values,
    })
    result = result.set_index('date').sort_index().dropna(subset=['ca_pct_gdp'])

    outpath = PROC_DIR / 'current_account_gdp.csv'
    result.to_csv(outpath)
    print(f"  Current account: {len(result)} quarters, {result.index[0].date()} to {result.index[-1].date()}")
    print(f"  Latest CA/GDP: {result['ca_pct_gdp'].iloc[-1]:.1f}%")
    return result


def process_debt_to_gdp():
    """Clean and output federal debt-to-GDP ratio.

    Uses GFDEGDQ188S (already in percent).
    Output: debt_to_gdp.csv with columns: date, debt_gdp.
    """
    path = RAW_DIR / 'GFDEGDQ188S.csv'
    if not path.exists():
        print("  WARNING: GFDEGDQ188S.csv not found. Skipping debt-to-GDP processing.")
        return None

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')
    df.columns = ['debt_gdp']
    df = df.sort_index().dropna(subset=['debt_gdp'])

    # Sanity check: 20% to 200%
    out_of_bounds = (df['debt_gdp'] < 20) | (df['debt_gdp'] > 200)
    if out_of_bounds.any():
        print(f"  WARNING: {out_of_bounds.sum()} debt-to-GDP values outside 20-200% range.")

    outpath = PROC_DIR / 'debt_to_gdp.csv'
    df.to_csv(outpath)
    print(f"  Debt-to-GDP: {len(df)} quarters, {df.index[0].date()} to {df.index[-1].date()}")
    print(f"  Latest debt/GDP: {df['debt_gdp'].iloc[-1]:.1f}%")
    return df


def process_deficit_gdp():
    """Clean and output federal surplus/deficit as percent of GDP.

    Uses FYFSGDA188S (already in percent, negative = deficit).
    Output: deficit_gdp.csv with columns: date, deficit_gdp.
    """
    path = RAW_DIR / 'FYFSGDA188S.csv'
    if not path.exists():
        print("  WARNING: FYFSGDA188S.csv not found. Skipping deficit/GDP processing.")
        return None

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')
    df.columns = ['deficit_gdp']
    df = df.sort_index().dropna(subset=['deficit_gdp'])

    # Sanity check: -40% to +10%
    out_of_bounds = (df['deficit_gdp'] < -40) | (df['deficit_gdp'] > 10)
    if out_of_bounds.any():
        print(f"  WARNING: {out_of_bounds.sum()} deficit/GDP values outside -40% to +10% range.")

    outpath = PROC_DIR / 'deficit_gdp.csv'
    df.to_csv(outpath)
    print(f"  Deficit/GDP: {len(df)} annual observations, {df.index[0].date()} to {df.index[-1].date()}")
    print(f"  Latest deficit/GDP: {df['deficit_gdp'].iloc[-1]:.1f}%")
    return df


def process_r_minus_g():
    """Compute r − g: 10-year Treasury yield minus nominal GDP growth.

    r: DGS10 (10-year Treasury yield, daily → quarterly average)
    g: nominal GDP growth rate (annualized % change from GDP series)
    Output: r_minus_g.csv with columns: date, r_minus_g, yield_10y, ngdp_growth.
    """
    dgs10_path = RAW_DIR / 'DGS10.csv'
    gdp_path = RAW_DIR / 'GDP.csv'

    if not dgs10_path.exists() or not gdp_path.exists():
        print("  WARNING: DGS10.csv or GDP.csv not found. Skipping r−g processing.")
        return None

    # 10-year yield: daily → quarterly average
    yields = pd.read_csv(dgs10_path, parse_dates=['date'], index_col='date')
    yields.columns = ['yield_10y']
    yields['period'] = yields.index.to_period('Q')
    quarterly_yield = yields.groupby('period')['yield_10y'].mean()

    # Nominal GDP growth: annualized % change (quarter-over-quarter × 4)
    gdp = pd.read_csv(gdp_path, parse_dates=['date'], index_col='date')
    gdp.columns = ['gdp']
    gdp['period'] = gdp.index.to_period('Q')
    gdp_q = gdp.groupby('period')['gdp'].last()
    # Year-over-year growth rate (avoids seasonality issues with QoQ annualization)
    ngdp_growth = gdp_q.pct_change(periods=4) * 100

    # Align on quarterly periods
    combined = pd.DataFrame({
        'yield_10y': quarterly_yield,
        'ngdp_growth': ngdp_growth,
    }).dropna()

    combined['r_minus_g'] = combined['yield_10y'] - combined['ngdp_growth']

    # Convert period index to timestamp
    result = combined.copy()
    result.index = result.index.to_timestamp(how='end')
    result.index.name = 'date'

    # Sanity check: -30 to +20 range
    out_of_bounds = (result['r_minus_g'] < -30) | (result['r_minus_g'] > 20)
    if out_of_bounds.any():
        print(f"  WARNING: {out_of_bounds.sum()} r−g values outside -30 to +20 range.")

    outpath = PROC_DIR / 'r_minus_g.csv'
    result.to_csv(outpath)
    print(f"  r−g: {len(result)} quarters, {result.index[0].date()} to {result.index[-1].date()}")
    print(f"  Latest r−g: {result['r_minus_g'].iloc[-1]:.1f} pp")
    return result


def build_metadata(cofer=None, dxy=None, debt=None, fx=None, treasuries=None,
                   fed_holdings=None, current_account=None, debt_to_gdp=None,
                   deficit_gdp=None, r_minus_g=None):
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

    if treasuries is not None and len(treasuries) > 0:
        metadata["sources"]["treasuries"] = {
            "last_obs": str(treasuries.index[-1].date()),
            "source": "FRED FDHBFIN / FYGFDPUN"
        }

    if fed_holdings is not None and len(fed_holdings) > 0:
        metadata["sources"]["fed_holdings"] = {
            "last_obs": str(fed_holdings.index[-1].date()),
            "source": "FRED FDHBFRBN / FYGFDPUN"
        }

    if dxy is not None and len(dxy) > 0:
        metadata["sources"]["dxy"] = {
            "last_obs": str(dxy.index[-1].date()),
            "source": "FRED DTWEXBGS"
        }

    if current_account is not None and len(current_account) > 0:
        metadata["sources"]["current_account"] = {
            "last_obs": str(current_account.index[-1].date()),
            "source": "FRED NETFI / GDP"
        }

    if debt_to_gdp is not None and len(debt_to_gdp) > 0:
        metadata["sources"]["debt_to_gdp"] = {
            "last_obs": str(debt_to_gdp.index[-1].date()),
            "source": "FRED GFDEGDQ188S"
        }

    if deficit_gdp is not None and len(deficit_gdp) > 0:
        metadata["sources"]["deficit_gdp"] = {
            "last_obs": str(deficit_gdp.index[-1].date()),
            "source": "FRED FYFSGDA188S"
        }

    if r_minus_g is not None and len(r_minus_g) > 0:
        metadata["sources"]["r_minus_g"] = {
            "last_obs": str(r_minus_g.index[-1].date()),
            "source": "FRED DGS10 / GDP (computed)"
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
    treasuries = process_treasuries()
    fed_holdings = process_fed_holdings()
    ca = process_current_account()
    debt_gdp = process_debt_to_gdp()
    deficit = process_deficit_gdp()
    r_g = process_r_minus_g()

    build_metadata(cofer=cofer, dxy=dxy, debt=debt, fx=fx, treasuries=treasuries,
                   fed_holdings=fed_holdings, current_account=ca, debt_to_gdp=debt_gdp,
                   deficit_gdp=deficit, r_minus_g=r_g)


if __name__ == '__main__':
    process_all()
