# Dollar Dominance Dashboard

Automated data pipeline and interactive dashboard tracking U.S. dollar dominance across international finance.

**[View the live dashboard](https://bryanpcutsinger.github.io/dollar-dominance/)**

## Overview

The dashboard tracks four dimensions of dollar dominance:

- **Foreign exchange reserves** (IMF COFER) — USD share of global allocated reserves
- **FX market turnover** (BIS Triennial Survey) — USD share of daily foreign exchange trading
- **International debt securities** (BIS) — USD share of outstanding international bonds
- **Trade-weighted dollar index** (DXY via FRED) — Broad dollar strength over time

Three tabs present the data: **Snapshot** (current metrics and key takeaways), **Trends** (interactive Plotly charts), and **Methodology** (source descriptions and caveats).

## Quick Start

```bash
# 1. Set up FRED API key
cp .env.example .env
# Edit .env and add your FRED API key

# 2. Install dependencies
python3 -m pip install -r requirements.txt

# 3. Run full pipeline
python3 run_pipeline.py

# 4. Open dashboard
open output/index.html
```

## Pipeline Modes

| Command | What it does |
|---------|--------------|
| `python3 run_pipeline.py` | Full run: fetch + process + build |
| `python3 run_pipeline.py --no-fetch` | Rebuild from cached CSVs |
| `python3 run_pipeline.py --fetch-only` | Fetch data only |

## Data Sources

| Source | Method | Frequency |
|--------|--------|-----------|
| IMF COFER | SDMX API (DBnomics fallback) | Quarterly |
| BIS Debt Securities | Bulk CSV download | Quarterly |
| BIS FX Turnover | Hard-coded from survey | Every 3 years |
| FRED (DXY) | `fredapi` | Daily |

## Deployment

The dashboard is a single static HTML file served via GitHub Pages from `main/docs`.

A [GitHub Actions workflow](.github/workflows/update-dashboard.yml) runs the pipeline weekly (Monday 8 AM UTC) and commits any data changes automatically.

## Tech Stack

Python 3.11+, pandas, plotly, fredapi, requests.
