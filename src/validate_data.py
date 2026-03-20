"""
Post-pipeline data validation agent.

Independently verifies that pipeline data is accurate and current by:
1. Re-fetching sample values from live APIs and comparing against raw CSVs
2. Re-deriving processed values from raw data and comparing against processed CSVs
3. Checking staleness — whether last observation dates are within expected ranges

Usage:
    python -m src.validate_data          # Run standalone
    Called automatically by run_pipeline.py --validate
    Called with fix mode by run_pipeline.py --validate --fix
"""

import json
import os
import re
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import FRED_API_KEY, FRED_SERIES

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RAW_DIR = Path('data/raw')
PROC_DIR = Path('data/processed')

# How stale each source can be before we flag it (in days)
STALENESS_THRESHOLDS = {
    'DTWEXBGS': 10,     # Daily, allow weekends + holidays
    'DGS10': 10,        # Daily
    'FDHBFIN': 180,     # Quarterly, allow ~6 months lag
    'FYGFDPUN': 180,
    'FDHBFRBN': 180,
    'NETFI': 180,
    'GDP': 180,
    'GFDEGDQ188S': 180,
    'FYFSGDA188S': 400, # Annual, allow >1 year lag
    'cofer': 270,       # Quarterly, often delayed
    'bis_debt': 270,    # Quarterly, often delayed
}


class ValidationResult:
    """Collects pass/fail/warn results for a clean report."""

    def __init__(self):
        self.checks = []  # list of (status, source, message)
        self.fix_actions = set()  # sources that need re-fetching

    def passed(self, source, msg):
        self.checks.append(('PASS', source, msg))

    def failed(self, source, msg):
        self.checks.append(('FAIL', source, msg))

    def warn(self, source, msg):
        self.checks.append(('WARN', source, msg))

    def needs_fix(self, source_key):
        """Flag a source for re-fetching. Keys: 'fred', 'cofer', 'bis', 'process'."""
        self.fix_actions.add(source_key)

    def report(self):
        """Print a formatted validation report."""
        n_pass = sum(1 for s, _, _ in self.checks if s == 'PASS')
        n_fail = sum(1 for s, _, _ in self.checks if s == 'FAIL')
        n_warn = sum(1 for s, _, _ in self.checks if s == 'WARN')

        print("\n" + "=" * 70)
        print("  DATA VALIDATION REPORT")
        print("=" * 70)

        # Group by source
        sources = {}
        for status, source, msg in self.checks:
            sources.setdefault(source, []).append((status, msg))

        for source, items in sources.items():
            print(f"\n  [{source}]")
            for status, msg in items:
                icon = {'PASS': '✓', 'FAIL': '✗', 'WARN': '⚠'}[status]
                print(f"    {icon} {status}: {msg}")

        print("\n" + "-" * 70)
        print(f"  Summary: {n_pass} passed, {n_warn} warnings, {n_fail} failures")

        if n_fail > 0:
            print("  ⚠ ACTION REQUIRED: Some checks failed. Review data before publishing.")
        elif n_warn > 0:
            print("  Data looks good with minor warnings.")
        else:
            print("  All checks passed. Data verified.")

        print("=" * 70 + "\n")
        return n_fail == 0


# ---------------------------------------------------------------------------
# 1. FRED: re-fetch latest observations and compare against raw CSVs
# ---------------------------------------------------------------------------

def validate_fred(result):
    """Re-fetch the latest value for each FRED series and compare to raw CSV."""
    if FRED_API_KEY == 'YOUR_KEY_HERE':
        result.warn('FRED', 'API key not configured — skipping live verification')
        return

    from fredapi import Fred
    fred = Fred(api_key=FRED_API_KEY)

    for series_id in FRED_SERIES:
        csv_path = RAW_DIR / f'{series_id}.csv'

        # Check CSV exists
        if not csv_path.exists():
            result.failed('FRED', f'{series_id}: raw CSV missing')
            continue

        df_local = pd.read_csv(csv_path, parse_dates=['date'])
        if df_local.empty:
            result.failed('FRED', f'{series_id}: raw CSV is empty')
            continue

        local_last_date = df_local['date'].max()
        local_last_value = df_local.loc[df_local['date'] == local_last_date, 'value'].iloc[0]

        # Re-fetch latest observation from FRED
        try:
            live_data = fred.get_series(series_id)
            live_data = pd.to_numeric(live_data, errors='coerce').dropna()
            if live_data.empty:
                result.warn('FRED', f'{series_id}: live API returned no data')
                continue

            live_last_date = live_data.index[-1]
            live_last_value = live_data.iloc[-1]

            # Check 1: dates match (pipeline has latest available data)
            if pd.Timestamp(local_last_date) == pd.Timestamp(live_last_date):
                result.passed('FRED', f'{series_id}: latest date matches ({local_last_date.date()})')
            else:
                days_behind = (pd.Timestamp(live_last_date) - pd.Timestamp(local_last_date)).days
                if days_behind > 7:
                    # More than a week behind — trigger re-fetch
                    result.warn('FRED', f'{series_id}: pipeline is {days_behind} days behind '
                                f'(local: {local_last_date.date()}, live: {live_last_date.date()})')
                    result.needs_fix('fred')
                elif days_behind > 0:
                    result.warn('FRED', f'{series_id}: pipeline is {days_behind} days behind '
                                f'(local: {local_last_date.date()}, live: {live_last_date.date()})')
                else:
                    result.passed('FRED', f'{series_id}: latest date matches (within rounding)')

            # Check 2: values match for the local latest date
            # Look up local_last_date in the live data
            if pd.Timestamp(local_last_date) in live_data.index:
                live_val_at_local_date = live_data.loc[pd.Timestamp(local_last_date)]
                if abs(local_last_value - live_val_at_local_date) < 0.01:
                    result.passed('FRED', f'{series_id}: latest value verified ({local_last_value:.4f})')
                else:
                    result.failed('FRED', f'{series_id}: VALUE MISMATCH at {local_last_date.date()} — '
                                  f'local={local_last_value:.4f}, live={live_val_at_local_date:.4f}')
                    result.needs_fix('fred')

        except Exception as e:
            result.warn('FRED', f'{series_id}: live check failed ({e})')


# ---------------------------------------------------------------------------
# 2. IMF COFER: re-fetch and compare latest quarter
# ---------------------------------------------------------------------------

def validate_cofer(result):
    """Re-fetch COFER from IMF API and compare latest quarter to raw CSV."""
    csv_path = RAW_DIR / 'cofer_shares.csv'
    if not csv_path.exists():
        result.failed('COFER', 'raw CSV missing')
        return

    df_local = pd.read_csv(csv_path, index_col=0)
    if df_local.empty:
        result.failed('COFER', 'raw CSV is empty')
        return

    local_last_period = df_local.index[-1]
    local_usd = df_local.loc[local_last_period, 'usd']

    # Basic sanity: USD share should be between 40% and 75%
    if 40 < local_usd < 75:
        result.passed('COFER', f'USD share ({local_usd:.2f}%) in plausible range (40-75%)')
    else:
        result.failed('COFER', f'USD share ({local_usd:.2f}%) outside plausible range (40-75%)')

    # Check that shares sum to ~100% for latest period
    currency_cols = [c for c in df_local.columns if c in
                     ['usd', 'eur', 'cny', 'jpy', 'gbp', 'aud', 'cad', 'chf', 'other']]
    total = df_local.loc[local_last_period, currency_cols].sum()
    if abs(total - 100) < 2:
        result.passed('COFER', f'Currency shares sum to {total:.2f}% (≈100%)')
    else:
        result.failed('COFER', f'Currency shares sum to {total:.2f}% (expected ≈100%)')

    # Re-fetch from IMF API for independent verification
    try:
        from src.fetch_cofer import _fetch_imf_api
        df_live = _fetch_imf_api(max_retries=2)
        if df_live is not None and not df_live.empty:
            live_last_period = df_live.index[-1]
            if local_last_period == live_last_period:
                result.passed('COFER', f'Latest period matches live API ({local_last_period})')
            else:
                result.warn('COFER', f'Newer data available — local: {local_last_period}, '
                            f'live: {live_last_period}. Re-run pipeline to update.')
                result.needs_fix('cofer')

            # Compare USD share for the same period (use local's latest in live data)
            if local_last_period in df_live.index and 'usd' in df_live.columns:
                live_usd = df_live.loc[local_last_period, 'usd']
                diff = abs(local_usd - live_usd)
                if diff < 0.1:
                    result.passed('COFER', f'USD share verified against live API for '
                                  f'{local_last_period} ({local_usd:.2f}%)')
                elif diff < 2.0:
                    # IMF routinely revises past quarters — flag but don't fail
                    result.warn('COFER', f'USD share revised at {local_last_period} — '
                                f'local: {local_usd:.2f}%, live: {live_usd:.2f}% '
                                f'(likely IMF revision, re-run pipeline to update)')
                    result.needs_fix('cofer')
                else:
                    result.failed('COFER', f'USD share mismatch at {local_last_period} — '
                                  f'local: {local_usd:.2f}%, live: {live_usd:.2f}%')
                    result.needs_fix('cofer')
            elif local_last_period != live_last_period:
                pass  # Different periods — already warned above
            else:
                result.warn('COFER', f'Could not cross-check {local_last_period} in live data')
        else:
            result.warn('COFER', 'Live IMF API returned no data — skipping cross-check')
    except Exception as e:
        result.warn('COFER', f'Live COFER check failed ({e})')


# ---------------------------------------------------------------------------
# 3. Processed data: re-derive values from raw and compare
# ---------------------------------------------------------------------------

def validate_processed(result):
    """Re-derive key processed values from raw CSVs and compare."""

    # --- Treasury foreign share ---
    try:
        fdhbfin = pd.read_csv(RAW_DIR / 'FDHBFIN.csv', parse_dates=['date'])
        fygfdpun = pd.read_csv(RAW_DIR / 'FYGFDPUN.csv', parse_dates=['date'])
        proc = pd.read_csv(PROC_DIR / 'treasury_foreign_share.csv', parse_dates=['date'])

        if not fdhbfin.empty and not fygfdpun.empty and not proc.empty:
            # Re-derive: (FDHBFIN_billions * 1000 / FYGFDPUN_millions) * 100
            merged = fdhbfin.merge(fygfdpun, on='date', suffixes=('_foreign', '_public'))
            if not merged.empty:
                last = merged.iloc[-1]
                rederived = (last['value_foreign'] * 1000 / last['value_public']) * 100

                proc_last = proc.iloc[-1]['foreign_share']
                if abs(rederived - proc_last) < 0.5:
                    result.passed('Processed', f'Treasury foreign share verified '
                                  f'({proc_last:.2f}% vs re-derived {rederived:.2f}%)')
                else:
                    result.failed('Processed', f'Treasury foreign share mismatch — '
                                  f'processed: {proc_last:.2f}%, re-derived: {rederived:.2f}%')
                    result.needs_fix('process')
    except Exception as e:
        result.warn('Processed', f'Treasury foreign share check failed ({e})')

    # --- Current account / GDP ---
    try:
        netfi = pd.read_csv(RAW_DIR / 'NETFI.csv', parse_dates=['date'])
        gdp = pd.read_csv(RAW_DIR / 'GDP.csv', parse_dates=['date'])
        proc_ca = pd.read_csv(PROC_DIR / 'current_account_gdp.csv', parse_dates=['date'])

        if not netfi.empty and not gdp.empty and not proc_ca.empty:
            merged = netfi.merge(gdp, on='date', suffixes=('_ca', '_gdp'))
            if not merged.empty:
                last = merged.iloc[-1]
                rederived = (last['value_ca'] / last['value_gdp']) * 100
                proc_last = proc_ca.iloc[-1]['ca_pct_gdp']
                if abs(rederived - proc_last) < 0.5:
                    result.passed('Processed', f'Current account/GDP verified '
                                  f'({proc_last:.2f}% vs re-derived {rederived:.2f}%)')
                else:
                    result.failed('Processed', f'Current account/GDP mismatch — '
                                  f'processed: {proc_last:.2f}%, re-derived: {rederived:.2f}%')
                    result.needs_fix('process')
    except Exception as e:
        result.warn('Processed', f'Current account/GDP check failed ({e})')

    # --- Debt securities shares sum to ~100% ---
    try:
        proc_debt = pd.read_csv(PROC_DIR / 'debt_securities_shares.csv', parse_dates=['date'])
        if not proc_debt.empty:
            last = proc_debt.iloc[-1]
            total = last['usd'] + last['eur'] + last['other']
            if abs(total - 100) < 2:
                result.passed('Processed', f'BIS debt shares sum to {total:.1f}% (≈100%)')
            else:
                result.failed('Processed', f'BIS debt shares sum to {total:.1f}% (expected ≈100%)')
                result.needs_fix('process')
    except Exception as e:
        result.warn('Processed', f'BIS debt shares check failed ({e})')


# ---------------------------------------------------------------------------
# 4. Staleness checks
# ---------------------------------------------------------------------------

def validate_staleness(result):
    """Check that last observation dates are within expected update windows."""
    today = datetime.now()

    # FRED series
    for series_id, threshold_days in STALENESS_THRESHOLDS.items():
        if series_id in ('cofer', 'bis_debt'):
            continue  # handled separately below

        csv_path = RAW_DIR / f'{series_id}.csv'
        if not csv_path.exists():
            continue

        df = pd.read_csv(csv_path, parse_dates=['date'])
        if df.empty:
            continue

        last_date = df['date'].max()
        days_old = (today - last_date).days

        if days_old <= threshold_days:
            result.passed('Staleness', f'{series_id}: last obs {last_date.date()} '
                          f'({days_old}d ago, threshold {threshold_days}d)')
        else:
            result.warn('Staleness', f'{series_id}: last obs {last_date.date()} '
                        f'({days_old}d ago, exceeds {threshold_days}d threshold)')
            result.needs_fix('fred')

    # COFER
    cofer_path = RAW_DIR / 'cofer_shares.csv'
    if cofer_path.exists():
        df = pd.read_csv(cofer_path, index_col=0)
        if not df.empty:
            last_period = df.index[-1]  # e.g., "2024-Q3"
            # Parse quarter to approximate date
            try:
                year, q = last_period.split('-Q')
                approx_date = datetime(int(year), int(q) * 3, 28)
                days_old = (today - approx_date).days
                threshold = STALENESS_THRESHOLDS['cofer']
                if days_old <= threshold:
                    result.passed('Staleness', f'COFER: last period {last_period} '
                                  f'({days_old}d ago)')
                else:
                    result.warn('Staleness', f'COFER: last period {last_period} '
                                f'({days_old}d ago, exceeds {threshold}d threshold)')
                    result.needs_fix('cofer')
            except Exception:
                result.warn('Staleness', f'COFER: could not parse period "{last_period}"')

    # BIS debt securities — quarter columns in CSV headers
    bis_path = RAW_DIR / 'bis_debt_raw.csv'
    if bis_path.exists():
        try:
            cols = pd.read_csv(bis_path, nrows=0).columns.tolist()
            quarter_cols = [c for c in cols if re.match(r'^\d{4}-Q[1-4]$', c)]
            if quarter_cols:
                last_q = max(quarter_cols)  # e.g., "2025-Q3"
                year, q = last_q.split('-Q')
                approx_date = datetime(int(year), int(q) * 3, 28)
                days_old = (today - approx_date).days
                threshold = STALENESS_THRESHOLDS['bis_debt']
                if days_old <= threshold:
                    result.passed('Staleness', f'BIS debt: last period {last_q} '
                                  f'({days_old}d ago)')
                else:
                    result.warn('Staleness', f'BIS debt: last period {last_q} '
                                f'({days_old}d ago, exceeds {threshold}d threshold)')
                    result.needs_fix('bis')
            else:
                result.warn('Staleness', 'BIS debt: no quarter columns found in CSV')
        except Exception as e:
            result.warn('Staleness', f'BIS debt staleness check failed ({e})')


# ---------------------------------------------------------------------------
# 5. Metadata consistency
# ---------------------------------------------------------------------------

def validate_metadata(result):
    """Check that metadata.json exists and is consistent with actual data."""
    meta_path = PROC_DIR / 'metadata.json'
    if not meta_path.exists():
        result.warn('Metadata', 'metadata.json not found')
        return

    with open(meta_path) as f:
        meta = json.load(f)

    # Check timestamp is recent (within 24 hours if pipeline just ran)
    try:
        if 'last_updated' in meta:
            gen_time = datetime.fromisoformat(meta['last_updated'])
            hours_ago = (datetime.now() - gen_time).total_seconds() / 3600
            if hours_ago < 24:
                result.passed('Metadata', f'Generated {hours_ago:.1f} hours ago')
            else:
                result.warn('Metadata', f'Generated {hours_ago:.1f} hours ago (>24h)')
    except Exception as e:
        result.warn('Metadata', f'Timestamp check failed ({e})')

    # Check all expected processed files exist
    expected_files = [
        'cofer_shares.csv', 'dxy_weekly.csv', 'fx_turnover_triennial.csv',
        'debt_securities_shares.csv', 'treasury_foreign_share.csv',
        'treasury_fed_share.csv', 'current_account_gdp.csv',
        'debt_to_gdp.csv', 'deficit_gdp.csv', 'r_minus_g.csv',
    ]
    missing = [f for f in expected_files if not (PROC_DIR / f).exists()]
    if missing:
        result.failed('Metadata', f'Missing processed files: {", ".join(missing)}')
    else:
        result.passed('Metadata', f'All {len(expected_files)} processed files present')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _run_all_validators(result):
    """Run all validation checks against a ValidationResult."""
    validate_fred(result)
    validate_cofer(result)
    validate_processed(result)
    validate_staleness(result)
    validate_metadata(result)


def run_validation():
    """Run all validation checks and return True if no failures."""
    print("\n=== Running data validation ===")
    result = ValidationResult()
    _run_all_validators(result)
    return result.report()


# Sentinel files for mtime-based change detection
_SENTINEL_FILES = {
    'fred': RAW_DIR / 'DTWEXBGS.csv',
    'cofer': RAW_DIR / 'cofer_shares.csv',
    'bis': RAW_DIR / 'bis_debt_raw.csv',
}


def run_validation_with_fix():
    """Validate, auto-fix stale/mismatched data, verify, and rebuild if clean.

    Returns (success: bool, fixes_applied: list[str]).
    """
    from src.fetch_fred import fetch_all_fred
    from src.fetch_cofer import fetch_cofer
    from src.fetch_bis import fetch_bis_debt
    from src.process_data import process_all
    from src.build_dashboard import build_dashboard

    # --- Pass 1: Diagnose ---
    print("\n=== Validation Pass 1 (diagnose) ===")
    result = ValidationResult()
    _run_all_validators(result)
    result.report()

    if not result.fix_actions:
        print("  No fixes needed.")
        return True, []

    print(f"\n=== Applying fixes: {', '.join(sorted(result.fix_actions))} ===")

    # Record mtimes before fetching
    mtimes_before = {}
    for key, path in _SENTINEL_FILES.items():
        if path.exists():
            mtimes_before[key] = os.path.getmtime(str(path))

    # Re-fetch flagged sources
    fetchers = {
        'fred': ('FRED', fetch_all_fred),
        'cofer': ('COFER', fetch_cofer),
        'bis': ('BIS', fetch_bis_debt),
    }
    for key in sorted(result.fix_actions & fetchers.keys()):
        label, fn = fetchers[key]
        print(f"\n  Re-fetching {label}...")
        try:
            fn()
        except Exception as e:
            print(f"  WARNING: {label} re-fetch failed: {e}")

    # Check which sources actually changed (mtime comparison)
    sources_changed = []
    for key, path in _SENTINEL_FILES.items():
        if key not in result.fix_actions:
            continue
        if path.exists():
            new_mtime = os.path.getmtime(str(path))
            old_mtime = mtimes_before.get(key)
            if old_mtime is None or new_mtime != old_mtime:
                sources_changed.append(key)

    # Re-process if any raw data changed or 'process' was flagged
    if sources_changed or 'process' in result.fix_actions:
        print("\n  Re-processing data...")
        process_all()

    # --- Pass 2: Verify ---
    print("\n=== Validation Pass 2 (verify fixes) ===")
    result2 = ValidationResult()
    _run_all_validators(result2)
    pass2_ok = result2.report()

    fixes_applied = sources_changed + (['process'] if 'process' in result.fix_actions else [])

    # Build only if Pass 2 is clean
    if pass2_ok:
        print("\n=== Rebuilding dashboard (Pass 2 clean) ===")
        build_dashboard()
        # Copy to docs/ for GitHub Pages
        docs_dir = Path('docs')
        docs_dir.mkdir(exist_ok=True)
        shutil.copy2('output/index.html', docs_dir / 'index.html')
        print(f"  Copied to {docs_dir / 'index.html'} (GitHub Pages)")
    else:
        print("\n  Pass 2 still has failures — preserving existing dashboard.")

    return pass2_ok, fixes_applied


if __name__ == '__main__':
    success = run_validation()
    sys.exit(0 if success else 1)
