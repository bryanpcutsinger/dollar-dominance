# Dollar Dominance Dashboard

Automated data pipeline and static HTML dashboard tracking U.S. dollar dominance across international finance dimensions.

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

- `python3 run_pipeline.py` — Full: fetch + process + build
- `python3 run_pipeline.py --no-fetch` — Rebuild from cached CSVs
- `python3 run_pipeline.py --fetch-only` — Fetch only

## Data Sources

| Source | Method | Frequency |
|--------|--------|-----------|
| FRED (DXY, FDHBFIN, GFDEBTN) | `fredapi` | Daily → weekly (DXY), Quarterly (Treasuries) |
| IMF COFER | SDMX API (DBnomics fallback) | Quarterly |
| BIS Debt Securities | SDMX REST API | Quarterly |
| BIS FX Turnover | Hard-coded | Every 3 years |

## Dashboard Structure

Three tabs:
- **Snapshot** — Metric cards + key takeaways
- **Trends** — Interactive Plotly charts (COFER, FX Turnover, Debt Securities, Foreign Treasury Holdings, DXY) with per-chart takeaway panels
- **Methodology** — Data source descriptions and caveats

## Tech Stack

Python 3.11+, pandas, plotly, fredapi, requests. No database, no web framework.

## Deployment

GitHub Pages serves from `main/docs`. The pipeline copies `output/index.html` → `docs/index.html`.

**Update workflow:** Run pipeline → commit `docs/index.html` → push → site auto-updates.

## Key Decisions

- IMF legacy API (`dataservices.imf.org`) retired Nov 2025 — using IMF SDMX API as primary, DBnomics as fallback
- BIS SDMX REST API is now public (no API key required) — used for debt securities
- BIS debt data only has USD/EUR/Other breakdown at aggregate level
- COFER 2025Q3 methodology change marked on charts (unallocated category eliminated)
