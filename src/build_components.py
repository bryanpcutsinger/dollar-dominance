"""
Data-driven HTML components for the Dollar Dominance Dashboard.

Metric cards, key takeaways, and sticky header — all pure HTML/CSS, no Plotly.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PROC_DIR = Path('data/processed')


def _delta_html(delta, units="pp", horizon="YoY"):
    """Format a delta value with arrow, color, and time horizon label."""
    if abs(delta) < 0.05:
        return f'<span style="color:#999;">— 0.0 {units} {horizon}</span>'
    if delta > 0:
        arrow = "&#9650;"  # ▲
        color = "#0d7a3f"
        sign = "+"
    else:
        arrow = "&#9660;"  # ▼
        color = "#d62728"
        sign = ""
    return f'<span style="color:{color};">{arrow} {sign}{delta:.1f} {units} {horizon}</span>'


def build_metric_cards():
    """Return 4 metric cards as an HTML grid."""
    cards = []

    # Card 1: FX Reserves (COFER)
    cofer_path = PROC_DIR / 'cofer_shares.csv'
    if cofer_path.exists():
        df = pd.read_csv(cofer_path, parse_dates=['date'], index_col='date')
        usd = df['usd'].dropna()
        latest_val = usd.iloc[-1]
        latest_date = usd.index[-1]
        # YoY: 4 quarters back
        if len(usd) > 4:
            comp_val = usd.iloc[-5]
            delta = latest_val - comp_val
            delta_str = _delta_html(delta)
        else:
            delta_str = ""
        quarter = f"{latest_date.year}-Q{(latest_date.month - 1) // 3 + 1}"
        cards.append(f"""
        <div class="metric-card">
            <div class="category-badge badge-reserve">RESERVE</div>
            <div class="card-label">FX Reserves</div>
            <div class="card-value">{latest_val:.1f}%</div>
            <div class="card-delta">{delta_str}</div>
            <div class="card-date">{quarter} &middot; IMF COFER</div>
        </div>""")

    # Card 2: FX Turnover (BIS)
    fx_path = PROC_DIR / 'fx_turnover_triennial.csv'
    if fx_path.exists():
        df = pd.read_csv(fx_path)
        rows = df.dropna(subset=['usd'])
        if len(rows) >= 2:
            latest = rows.iloc[-1]
            prior = rows.iloc[-2]
            delta = latest['usd'] - prior['usd']
            horizon = f"vs {int(prior['year'])}"
            delta_str = _delta_html(delta, horizon=horizon)
            cards.append(f"""
        <div class="metric-card">
            <div class="category-badge badge-trade">TRADE</div>
            <div class="card-label">FX Turnover</div>
            <div class="card-value">{latest['usd']:.1f}%</div>
            <div class="card-delta">{delta_str}</div>
            <div class="card-date">{int(latest['year'])} BIS Survey</div>
        </div>""")
        elif len(rows) == 1:
            latest = rows.iloc[-1]
            cards.append(f"""
        <div class="metric-card">
            <div class="category-badge badge-trade">TRADE</div>
            <div class="card-label">FX Turnover</div>
            <div class="card-value">{latest['usd']:.1f}%</div>
            <div class="card-delta"></div>
            <div class="card-date">{int(latest['year'])} BIS Survey</div>
        </div>""")

    # Card 3: Debt Securities (BIS)
    debt_path = PROC_DIR / 'debt_securities_shares.csv'
    if debt_path.exists():
        df = pd.read_csv(debt_path, parse_dates=['date'], index_col='date')
        usd = df['usd'].dropna()
        latest_val = usd.iloc[-1]
        latest_date = usd.index[-1]
        if len(usd) > 4:
            delta = latest_val - usd.iloc[-5]
            delta_str = _delta_html(delta)
        else:
            delta_str = ""
        quarter = f"{latest_date.year}-Q{(latest_date.month - 1) // 3 + 1}"
        cards.append(f"""
        <div class="metric-card">
            <div class="category-badge badge-finance">FINANCE</div>
            <div class="card-label">Debt Securities</div>
            <div class="card-value">{latest_val:.1f}%</div>
            <div class="card-delta">{delta_str}</div>
            <div class="card-date">{quarter} &middot; BIS</div>
        </div>""")

    # Card 4: Dollar Index (DXY)
    dxy_path = PROC_DIR / 'dxy_weekly.csv'
    if dxy_path.exists():
        df = pd.read_csv(dxy_path, parse_dates=['date'], index_col='date')
        dxy = df['dxy'].dropna()
        latest_val = dxy.iloc[-1]
        latest_date = dxy.index[-1]
        # YoY: ~52 weeks back
        if len(dxy) > 52:
            comp_val = dxy.iloc[-53]
            delta_pct = (latest_val - comp_val) / comp_val * 100
            delta_str = _delta_html(delta_pct)
        else:
            delta_str = ""
        date_str = latest_date.strftime('%b %d, %Y')
        cards.append(f"""
        <div class="metric-card">
            <div class="category-badge badge-index">INDEX</div>
            <div class="card-label">Dollar Index (DXY)</div>
            <div class="card-value">{latest_val:.1f}</div>
            <div class="card-delta">{delta_str}</div>
            <div class="card-date">{date_str} &middot; FRED</div>
        </div>""")

    if not cards:
        return ""

    return '<div class="metric-cards-grid">' + ''.join(cards) + '</div>'


def build_key_takeaways():
    """Return 4 factual template sentences filled from data."""
    takeaways = []

    # 1. COFER
    cofer_path = PROC_DIR / 'cofer_shares.csv'
    if cofer_path.exists():
        df = pd.read_csv(cofer_path, parse_dates=['date'], index_col='date')
        usd = df['usd'].dropna()
        if len(usd) > 4:
            latest = usd.iloc[-1]
            latest_date = usd.index[-1]
            comp = usd.iloc[-5]
            quarter = f"{latest_date.year}-Q{(latest_date.month - 1) // 3 + 1}"
            delta = latest - comp
            direction = "down" if delta < 0 else "up"
            takeaways.append(
                f"Central banks held {latest:.1f}% of their foreign exchange reserves in dollars as of {quarter}, "
                f"{direction} {abs(delta):.1f} pp from a year ago."
            )

    # 2. FX Turnover
    fx_path = PROC_DIR / 'fx_turnover_triennial.csv'
    if fx_path.exists():
        df = pd.read_csv(fx_path).dropna(subset=['usd'])
        if len(df) >= 2:
            latest = df.iloc[-1]
            prior = df.iloc[-2]
            delta = latest['usd'] - prior['usd']
            direction = "down" if delta < 0 else "up"
            takeaways.append(
                f"The dollar was on one side of {latest['usd']:.1f}% of all currency trades worldwide "
                f"in {int(latest['year'])}, {direction} {abs(delta):.1f} pp from the prior survey in {int(prior['year'])}."
            )

    # 3. Debt Securities
    debt_path = PROC_DIR / 'debt_securities_shares.csv'
    if debt_path.exists():
        df = pd.read_csv(debt_path, parse_dates=['date'], index_col='date')
        usd = df['usd'].dropna()
        if len(usd) > 4:
            latest = usd.iloc[-1]
            latest_date = usd.index[-1]
            comp = usd.iloc[-5]
            quarter = f"{latest_date.year}-Q{(latest_date.month - 1) // 3 + 1}"
            delta = latest - comp
            direction = "down" if delta < 0 else "up"
            takeaways.append(
                f"{latest:.1f}% of international bonds and notes were denominated in dollars as of {quarter}, "
                f"{direction} {abs(delta):.1f} pp from a year ago."
            )

    # 4. DXY
    dxy_path = PROC_DIR / 'dxy_weekly.csv'
    if dxy_path.exists():
        df = pd.read_csv(dxy_path, parse_dates=['date'], index_col='date')
        dxy = df['dxy'].dropna()
        if len(dxy) > 52:
            latest = dxy.iloc[-1]
            latest_date = dxy.index[-1]
            comp = dxy.iloc[-53]
            delta_pct = (latest - comp) / comp * 100
            direction = "down" if delta_pct < 0 else "up"
            date_str = latest_date.strftime('%B %d, %Y')
            takeaways.append(
                f"The dollar's value against a broad basket of trading-partner currencies "
                f"is {direction} {abs(delta_pct):.1f}% over the past year (index: {latest:.1f} as of {date_str})."
            )

    if not takeaways:
        return ""

    items = ''.join(f'<li>{t}</li>' for t in takeaways)
    return f"""
    <div class="key-takeaways">
        <h3>Key Takeaways</h3>
        <ul>{items}</ul>
    </div>"""


def build_sticky_header():
    """Return sticky header HTML + JS. Shows 3 key values on scroll."""
    # Read data for the 3 values
    values = []

    cofer_path = PROC_DIR / 'cofer_shares.csv'
    if cofer_path.exists():
        df = pd.read_csv(cofer_path, parse_dates=['date'], index_col='date')
        latest = df['usd'].dropna().iloc[-1]
        values.append(f'<span class="sticky-item"><span class="sticky-label">FX Reserves</span> <span class="sticky-value">{latest:.1f}%</span></span>')

    fx_path = PROC_DIR / 'fx_turnover_triennial.csv'
    if fx_path.exists():
        df = pd.read_csv(fx_path).dropna(subset=['usd'])
        latest = df.iloc[-1]['usd']
        values.append(f'<span class="sticky-item"><span class="sticky-label">FX Turnover</span> <span class="sticky-value">{latest:.1f}%</span></span>')

    dxy_path = PROC_DIR / 'dxy_weekly.csv'
    if dxy_path.exists():
        df = pd.read_csv(dxy_path, parse_dates=['date'], index_col='date')
        latest = df['dxy'].dropna().iloc[-1]
        values.append(f'<span class="sticky-item"><span class="sticky-label">DXY</span> <span class="sticky-value">{latest:.1f}</span></span>')

    if not values:
        return ""

    separator = '<span class="sticky-sep">|</span>'
    return f"""
    <div id="sticky-header" class="sticky-header">
        <div class="sticky-inner">
            <span class="sticky-title">Dollar Dominance</span>
            {separator.join(values)}
        </div>
    </div>"""


def build_cofer_takeaways():
    """Return a takeaway panel for the COFER stacked area chart."""
    path = PROC_DIR / 'cofer_shares.csv'
    if not path.exists():
        return ""

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')
    usd = df['usd'].dropna()
    if len(usd) < 5:
        return ""

    latest_val = usd.iloc[-1]
    latest_date = usd.index[-1]
    quarter = f"{latest_date.year}-Q{(latest_date.month - 1) // 3 + 1}"

    # YoY change
    comp_val = usd.iloc[-5]
    delta = latest_val - comp_val
    direction = "up" if delta > 0 else "down"

    # EUR share
    eur = df['eur'].dropna().iloc[-1] if 'eur' in df.columns else None
    eur_bullet = f"<li>The euro, the nearest competitor, accounts for {eur:.1f}% of allocated reserves.</li>" if eur else ""

    # CNY share + trajectory
    cny_bullet = ""
    if 'cny' in df.columns:
        cny = df['cny'].dropna()
        if len(cny) >= 5:
            cny_latest = cny.iloc[-1]
            cny_delta = cny_latest - cny.iloc[-5]
            cny_dir = "rising" if cny_delta > 0 else "declining"
            cny_bullet = f"<li>The Chinese yuan stands at {cny_latest:.1f}%, {cny_dir} over the past year ({cny_delta:+.1f} pp).</li>"

    return f"""
    <div class="key-takeaways">
        <h3>FX Reserves</h3>
        <ul>
            <li>The U.S. dollar comprised {latest_val:.1f}% of global allocated reserves as of {quarter}.</li>
            <li>That is {direction} {abs(delta):.1f} pp from a year ago.</li>
            {eur_bullet}
            {cny_bullet}
        </ul>
    </div>"""


def build_fx_takeaways():
    """Return a takeaway panel for the FX turnover bar chart."""
    path = PROC_DIR / 'fx_turnover_triennial.csv'
    if not path.exists():
        return ""

    df = pd.read_csv(path).dropna(subset=['usd'])
    if len(df) < 2:
        return ""

    latest = df.iloc[-1]
    prior = df.iloc[-2]
    delta = latest['usd'] - prior['usd']
    direction = "up" if delta > 0 else "down"

    eur_val = latest['eur']
    latest_year = int(latest['year'])
    prior_year = int(prior['year'])
    next_survey = latest_year + 3

    return f"""
    <div class="key-takeaways">
        <h3>FX Turnover</h3>
        <ul>
            <li>The dollar was on one side of {latest['usd']:.1f}% of all FX transactions in the {latest_year} BIS survey.</li>
            <li>That is {direction} {abs(delta):.1f} pp from the prior survey in {prior_year}.</li>
            <li>The euro was the second-most traded currency at {eur_val:.1f}%.</li>
            <li>The BIS Triennial Survey is conducted every three years; the next survey is expected in {next_survey}.</li>
        </ul>
    </div>"""


def build_debt_takeaways():
    """Return a takeaway panel for the debt securities chart."""
    path = PROC_DIR / 'debt_securities_shares.csv'
    if not path.exists():
        return ""

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')
    usd = df['usd'].dropna()
    if len(usd) < 5:
        return ""

    latest_val = usd.iloc[-1]
    latest_date = usd.index[-1]
    quarter = f"{latest_date.year}-Q{(latest_date.month - 1) // 3 + 1}"

    comp_val = usd.iloc[-5]
    delta = latest_val - comp_val
    direction = "up" if delta > 0 else "down"

    eur_val = df['eur'].dropna().iloc[-1] if 'eur' in df.columns else None
    eur_bullet = f"<li>Euro-denominated securities account for {eur_val:.1f}% of the total.</li>" if eur_val else ""

    return f"""
    <div class="key-takeaways">
        <h3>Debt Securities</h3>
        <ul>
            <li>{latest_val:.1f}% of international debt securities were denominated in dollars as of {quarter}.</li>
            <li>That is {direction} {abs(delta):.1f} pp from a year ago.</li>
            {eur_bullet}
            <li>BIS data provides only a USD/EUR/Other breakdown at the aggregate level.</li>
        </ul>
    </div>"""


def build_dxy_takeaways():
    """Return a takeaway panel for the DXY chart."""
    path = PROC_DIR / 'dxy_weekly.csv'
    if not path.exists():
        return ""

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')
    dxy = df['dxy'].dropna()
    if len(dxy) < 53:
        return ""

    latest_val = dxy.iloc[-1]
    latest_date = dxy.index[-1]
    date_str = latest_date.strftime('%B %d, %Y')

    comp_val = dxy.iloc[-53]
    delta_pct = (latest_val - comp_val) / comp_val * 100
    direction = "up" if delta_pct > 0 else "down"

    all_time_high = dxy.max()
    all_time_low = dxy.min()
    high_date = dxy.idxmax().strftime('%b %Y')
    low_date = dxy.idxmin().strftime('%b %Y')

    return f"""
    <div class="key-takeaways">
        <h3>Dollar Index</h3>
        <ul>
            <li>The broad dollar index stood at {latest_val:.1f} as of {date_str}.</li>
            <li>That is {direction} {abs(delta_pct):.1f}% from a year ago.</li>
            <li>Within this dataset, the index ranged from {all_time_low:.1f} ({low_date}) to {all_time_high:.1f} ({high_date}).</li>
            <li>DTWEXBGS is a trade-weighted broad index covering 26 currencies, published by the Federal Reserve.</li>
        </ul>
    </div>"""


