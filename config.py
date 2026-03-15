import os
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _read_fred_key_from_claude_md():
    """Pull FRED API key from ~/.claude/CLAUDE.md if present."""
    claude_md = Path.home() / '.claude' / 'CLAUDE.md'
    if not claude_md.exists():
        return None
    text = claude_md.read_text()
    # Matches "- **FRED** <key>" in the API Keys section
    match = re.search(r'\*\*FRED\*\*\s+([a-f0-9]{32})', text)
    return match.group(1) if match else None


# FRED API key — checks: 1) environment variable, 2) .env file, 3) CLAUDE.md
FRED_API_KEY = os.environ.get('FRED_API_KEY', 'YOUR_KEY_HERE')
if FRED_API_KEY == 'YOUR_KEY_HERE':
    _key = _read_fred_key_from_claude_md()
    if _key:
        FRED_API_KEY = _key

# FRED series to fetch
FRED_SERIES = {
    'DTWEXBGS': 'Nominal Broad U.S. Dollar Index',
    'FDHBFIN': 'Federal Debt Held by Foreign and International Investors',
    'FYGFDPUN': 'Federal Debt Held by the Public',
    'FDHBFRBN': 'Federal Debt Held by Federal Reserve Banks',
    'NETFI': 'Balance on Current Account, NIPAs',
    'GDP': 'Gross Domestic Product',
    'GFDEGDQ188S': 'Federal Debt: Total Public Debt as Percent of GDP',
    'FYFSGDA188S': 'Federal Surplus or Deficit as Percent of GDP',
    'DGS10': 'Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity',
}

# IMF COFER — primary source is IMF SDMX API, DBnomics as fallback
IMF_SDMX_BASE = "https://api.imf.org/external/sdmx/2.1"
DBNOMICS_BASE = "https://api.db.nomics.world/v22"
COFER_DATASET = "IMF/COFER"

# BIS — bulk CSV download only (SDMX API not publicly available)
BIS_BULK_DEBT_URL = "https://data.bis.org/static/bulk/WS_DEBT_SEC2_PUB_csv_col.zip"

# Chart color palette
COLORS = {
    'USD': '#0f5499',   # Institutional blue
    'EUR': '#66a61e',   # Muted green
    'CNY': '#d92020',   # Red
    'JPY': '#e6a000',   # Amber
    'GBP': '#7b5ea7',   # Purple
    'CHF': '#a0522d',   # Sienna
    'AUD': '#c45b8a',   # Rose
    'CAD': '#8a9a2e',   # Olive
    'Other': '#8c8c8c', # Gray
    'Fed': '#8c6bb1',       # Purple (Fed holdings)
    'Foreign': '#0f5499',   # Blue (foreign holdings)
    'DomesticPrivate': '#b0b0b0',  # Gray (domestic private)
    'CurrentAccount': '#2563eb',    # Blue (current account)
    'DebtGDP': '#dc2626',           # Red (debt-to-GDP)
    'Deficit': '#d97706',           # Amber (deficit/GDP)
    'RminusG': '#7c3aed',          # Violet (r minus g)
}

# Event markers for time series charts
EVENTS = {
    '1999-01-01': 'Euro introduced',
    '2008-09-15': 'Lehman (GFC)',
    '2020-03-11': 'COVID-19',
    '2022-02-24': 'Russia sanctions',
    '2025-04-02': 'Tariff escalation',
    '2025-07-01': 'COFER methodology change',
}
