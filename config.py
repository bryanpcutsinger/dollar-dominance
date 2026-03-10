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
    'GFDEBTN': 'Federal Debt: Total Public Debt',
}

# IMF COFER — primary source is IMF SDMX API, DBnomics as fallback
IMF_SDMX_BASE = "https://api.imf.org/external/sdmx/2.1"
DBNOMICS_BASE = "https://api.db.nomics.world/v22"
COFER_DATASET = "IMF/COFER"

# BIS — bulk CSV download only (SDMX API not publicly available)
BIS_BULK_DEBT_URL = "https://data.bis.org/static/bulk/WS_DEBT_SEC2_PUB_csv_col.zip"

# Chart color palette
COLORS = {
    'USD': '#1f77b4',   # Blue
    'EUR': '#2ca02c',   # Green
    'CNY': '#d62728',   # Red
    'JPY': '#ff7f0e',   # Orange
    'GBP': '#9467bd',   # Purple
    'CHF': '#8c564b',   # Brown
    'AUD': '#e377c2',   # Pink
    'CAD': '#bcbd22',   # Yellow-green
    'Other': '#7f7f7f', # Gray
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
