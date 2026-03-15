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
        return f'<span style="color:#737385;">— 0.0 {units} {horizon}</span>'
    if delta > 0:
        arrow = "&#9650;"  # ▲
        color = "#0d7a3f"
        sign = "+"
    else:
        arrow = "&#9660;"  # ▼
        color = "#c22a2a"
        sign = ""
    return f'<span style="color:{color};">{arrow} {sign}{delta:.1f} {units} {horizon}</span>'


def build_hero_svg(last_updated):
    """Return the hero banner HTML with inline SVG background."""
    return f"""<header class="hero-banner">
    <svg class="hero-bg" viewBox="0 0 1400 180" preserveAspectRatio="xMidYMid slice"
         xmlns="http://www.w3.org/2000/svg" aria-hidden="true" role="presentation">
        <defs>
            <linearGradient id="hero-grad" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stop-color="#0f5499"/>
                <stop offset="70%" stop-color="#1a6bc4"/>
                <stop offset="100%" stop-color="#0f5499" stop-opacity="0.85"/>
            </linearGradient>
        </defs>
        <rect width="1400" height="180" fill="url(#hero-grad)"/>
        <path d="M300,180 L300,155 L360,150 L420,140 L480,135 L480,180Z" fill="rgba(255,255,255,0.12)"/>
        <rect x="560" y="150" width="30" height="30" rx="2" fill="rgba(255,255,255,0.12)"/>
        <rect x="598" y="140" width="30" height="40" rx="2" fill="rgba(255,255,255,0.12)"/>
        <rect x="636" y="155" width="30" height="25" rx="2" fill="rgba(255,255,255,0.12)"/>
        <path d="M750,180 L750,160 Q800,145 850,140 L850,180Z" fill="rgba(255,255,255,0.12)"/>
        <polyline points="940,165 980,155 1020,148 1060,152 1100,158" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="2.5" stroke-linecap="round"/>
        <polyline points="1150,160 1175,150 1200,162 1225,145 1250,155" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="2.5" stroke-linecap="round"/>
        <text x="1100" y="110" font-size="200" font-weight="900" fill="rgba(255,255,255,0.08)" font-family="Arial,sans-serif">$</text>
    </svg>
    <div class="hero-content">
        <h1>The Treasury Standard</h1>
        <p class="subtitle">Monitoring dollar dominance across reserves, transactions, debt markets, foreign demand, and the structural foundations of the international monetary system</p>
        <p class="meta-line">Last updated: {last_updated}</p>
    </div>
</header>"""


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
        <div class="metric-card" style="border-left-color: #0f5499;">
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
        <div class="metric-card" style="border-left-color: #b07800;">
            <div class="category-badge badge-trade">TRADE</div>
            <div class="card-label">FX Turnover</div>
            <div class="card-value">{latest['usd']:.1f}%</div>
            <div class="card-delta">{delta_str}</div>
            <div class="card-date">{int(latest['year'])} BIS Survey</div>
        </div>""")
        elif len(rows) == 1:
            latest = rows.iloc[-1]
            cards.append(f"""
        <div class="metric-card" style="border-left-color: #b07800;">
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
        <div class="metric-card" style="border-left-color: #5b3e8a;">
            <div class="category-badge badge-finance">FINANCE</div>
            <div class="card-label">Debt Securities</div>
            <div class="card-value">{latest_val:.1f}%</div>
            <div class="card-delta">{delta_str}</div>
            <div class="card-date">{quarter} &middot; BIS</div>
        </div>""")

    # Card 4: Foreign Treasury Holdings (FRED)
    treas_path = PROC_DIR / 'treasury_foreign_share.csv'
    if treas_path.exists():
        df = pd.read_csv(treas_path, parse_dates=['date'], index_col='date')
        share = df['foreign_share'].dropna()
        latest_val = share.iloc[-1]
        latest_date = share.index[-1]
        latest_period = latest_date.to_period('Q')
        # YoY: match by quarter period (4 quarters back)
        target_period = latest_period - 4
        yoy_matches = share[share.index.to_period('Q') == target_period]
        if len(yoy_matches) > 0:
            delta = latest_val - yoy_matches.iloc[0]
            delta_str = _delta_html(delta)
        else:
            delta_str = ""
        quarter = f"{latest_date.year}-Q{(latest_date.month - 1) // 3 + 1}"
        cards.append(f"""
        <div class="metric-card" style="border-left-color: #0a6a5a;">
            <div class="category-badge badge-demand">DEMAND</div>
            <div class="card-label">Foreign Treasury Holdings</div>
            <div class="card-value">{latest_val:.1f}%</div>
            <div class="card-delta">{delta_str}</div>
            <div class="card-date">{quarter} &middot; FRED</div>
        </div>""")

    # Card 5: Fed Treasury Holdings (FRED) — independent CSV
    fed_path = PROC_DIR / 'treasury_fed_share.csv'
    if fed_path.exists():
        df_fed = pd.read_csv(fed_path, parse_dates=['date'], index_col='date')
        fed = df_fed['fed_share'].dropna()
        if len(fed) > 0:
            fed_val = fed.iloc[-1]
            fed_date = fed.index[-1]
            fed_period = fed_date.to_period('Q')
            fed_target = fed_period - 4
            fed_yoy = fed[fed.index.to_period('Q') == fed_target]
            if len(fed_yoy) > 0:
                fed_delta = fed_val - fed_yoy.iloc[0]
                fed_delta_str = _delta_html(fed_delta)
            else:
                fed_delta_str = ""
            fed_quarter = f"{fed_date.year}-Q{(fed_date.month - 1) // 3 + 1}"
            cards.append(f"""
        <div class="metric-card" style="border-left-color: #8c6bb1;">
            <div class="category-badge badge-fed">FED</div>
            <div class="card-label">Fed Treasury Holdings</div>
            <div class="card-value">{fed_val:.1f}%</div>
            <div class="card-delta">{fed_delta_str}</div>
            <div class="card-date">{fed_quarter} &middot; FRED</div>
        </div>""")

    # Card 6: Current Account (% of GDP)
    ca_path = PROC_DIR / 'current_account_gdp.csv'
    if ca_path.exists():
        df_ca = pd.read_csv(ca_path, parse_dates=['date'], index_col='date')
        ca = df_ca['ca_pct_gdp'].dropna()
        if len(ca) > 0:
            ca_val = ca.iloc[-1]
            ca_date = ca.index[-1]
            ca_quarter = f"{ca_date.year}-Q{(ca_date.month - 1) // 3 + 1}"
            if len(ca) > 4:
                ca_delta = ca_val - ca.iloc[-5]
                ca_delta_str = _delta_html(ca_delta)
            else:
                ca_delta_str = ""
            cards.append(f"""
        <div class="metric-card" style="border-left-color: #2563eb;">
            <div class="category-badge badge-structural">STRUCTURAL</div>
            <div class="card-label">Current Account (% of GDP)</div>
            <div class="card-value">{ca_val:.1f}%</div>
            <div class="card-delta">{ca_delta_str}</div>
            <div class="card-date">{ca_quarter} &middot; FRED</div>
        </div>""")

    # Card 7: Federal Debt-to-GDP
    dtg_path = PROC_DIR / 'debt_to_gdp.csv'
    if dtg_path.exists():
        df_dtg = pd.read_csv(dtg_path, parse_dates=['date'], index_col='date')
        dtg = df_dtg['debt_gdp'].dropna()
        if len(dtg) > 0:
            dtg_val = dtg.iloc[-1]
            dtg_date = dtg.index[-1]
            dtg_quarter = f"{dtg_date.year}-Q{(dtg_date.month - 1) // 3 + 1}"
            if len(dtg) > 4:
                dtg_delta = dtg_val - dtg.iloc[-5]
                dtg_delta_str = _delta_html(dtg_delta)
            else:
                dtg_delta_str = ""
            cards.append(f"""
        <div class="metric-card" style="border-left-color: #dc2626;">
            <div class="category-badge badge-structural">STRUCTURAL</div>
            <div class="card-label">Federal Debt-to-GDP</div>
            <div class="card-value">{dtg_val:.1f}%</div>
            <div class="card-delta">{dtg_delta_str}</div>
            <div class="card-date">{dtg_quarter} &middot; FRED</div>
        </div>""")

    # Card 8: Federal Deficit/GDP
    def_path = PROC_DIR / 'deficit_gdp.csv'
    if def_path.exists():
        df_def = pd.read_csv(def_path, parse_dates=['date'], index_col='date')
        deficit = df_def['deficit_gdp'].dropna()
        if len(deficit) > 0:
            def_val = deficit.iloc[-1]
            def_date = deficit.index[-1]
            def_year = str(def_date.year)
            if len(deficit) > 1:
                def_delta = def_val - deficit.iloc[-2]
                def_delta_str = _delta_html(def_delta, horizon="YoY")
            else:
                def_delta_str = ""
            cards.append(f"""
        <div class="metric-card" style="border-left-color: #d97706;">
            <div class="category-badge badge-structural">STRUCTURAL</div>
            <div class="card-label">Federal Deficit (% of GDP)</div>
            <div class="card-value">{def_val:.1f}%</div>
            <div class="card-delta">{def_delta_str}</div>
            <div class="card-date">{def_year} &middot; FRED</div>
        </div>""")

    # Card 9: r − g
    rg_path = PROC_DIR / 'r_minus_g.csv'
    if rg_path.exists():
        df_rg = pd.read_csv(rg_path, parse_dates=['date'], index_col='date')
        rg = df_rg['r_minus_g'].dropna()
        if len(rg) > 0:
            rg_val = rg.iloc[-1]
            rg_date = rg.index[-1]
            rg_quarter = f"{rg_date.year}-Q{(rg_date.month - 1) // 3 + 1}"
            if len(rg) > 4:
                rg_delta = rg_val - rg.iloc[-5]
                rg_delta_str = _delta_html(rg_delta)
            else:
                rg_delta_str = ""
            sign_label = "r > g" if rg_val > 0 else "r < g"
            cards.append(f"""
        <div class="metric-card" style="border-left-color: #7c3aed;">
            <div class="category-badge badge-structural">STRUCTURAL</div>
            <div class="card-label">r − g ({sign_label})</div>
            <div class="card-value">{rg_val:.1f} pp</div>
            <div class="card-delta">{rg_delta_str}</div>
            <div class="card-date">{rg_quarter} &middot; FRED</div>
        </div>""")

    # Card 10: Dollar Index (DXY)
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
        <div class="metric-card" style="border-left-color: #3a6e1e;">
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

    # 4. Foreign Treasury Holdings
    treas_path = PROC_DIR / 'treasury_foreign_share.csv'
    if treas_path.exists():
        df = pd.read_csv(treas_path, parse_dates=['date'], index_col='date')
        share = df['foreign_share'].dropna()
        if len(share) > 0:
            latest = share.iloc[-1]
            latest_date = share.index[-1]
            latest_period = latest_date.to_period('Q')
            quarter = f"{latest_date.year}-Q{(latest_date.month - 1) // 3 + 1}"
            # YoY: match by quarter period
            target_period = latest_period - 4
            yoy_matches = share[share.index.to_period('Q') == target_period]
            if len(yoy_matches) > 0:
                delta = latest - yoy_matches.iloc[0]
                direction = "down" if delta < 0 else "up"
                takeaways.append(
                    f"Foreign investors held {latest:.1f}% of publicly held federal debt as of {quarter}, "
                    f"{direction} {abs(delta):.1f} pp from a year ago."
                )

    # 5. DXY
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

    treas_path = PROC_DIR / 'treasury_foreign_share.csv'
    if treas_path.exists():
        df = pd.read_csv(treas_path, parse_dates=['date'], index_col='date')
        latest = df['foreign_share'].dropna().iloc[-1]
        values.append(f'<span class="sticky-item"><span class="sticky-label">Foreign Treas.</span> <span class="sticky-value">{latest:.1f}%</span></span>')

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
            <span class="sticky-title">The Treasury Standard</span>
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


def build_treasuries_takeaways():
    """Return a takeaway panel for the foreign Treasury holdings chart."""
    path = PROC_DIR / 'treasury_foreign_share.csv'
    if not path.exists():
        return ""

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')
    share = df['foreign_share'].dropna()
    if len(share) < 5:
        return ""

    latest_val = share.iloc[-1]
    latest_date = share.index[-1]
    quarter = f"{latest_date.year}-Q{(latest_date.month - 1) // 3 + 1}"

    # YoY change by quarter period
    latest_period = latest_date.to_period('Q')
    target_period = latest_period - 4
    yoy_matches = share[share.index.to_period('Q') == target_period]
    if len(yoy_matches) > 0:
        delta = latest_val - yoy_matches.iloc[0]
        direction = "up" if delta > 0 else "down"
        yoy_bullet = f"<li>That is {direction} {abs(delta):.1f} pp from a year ago.</li>"
    else:
        yoy_bullet = ""

    # Historical peak
    peak_val = share.max()
    peak_date = share.idxmax()
    peak_quarter = f"{peak_date.year}-Q{(peak_date.month - 1) // 3 + 1}"

    return f"""
    <div class="key-takeaways">
        <h3>Foreign Treasury Holdings</h3>
        <ul>
            <li>Foreign investors held {latest_val:.1f}% of publicly held federal debt as of {quarter}.</li>
            {yoy_bullet}
            <li>The historical peak was {peak_val:.1f}% in {peak_quarter}.</li>
            <li>Source: FRED series FDHBFIN (foreign holdings) and FYGFDPUN (debt held by public).</li>
        </ul>
    </div>"""


def build_fed_holdings_takeaways():
    """Return a takeaway panel for the Fed Treasury holdings chart."""
    path = PROC_DIR / 'treasury_fed_share.csv'
    if not path.exists():
        return ""

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')
    fed = df['fed_share'].dropna()
    if len(fed) < 5:
        return ""

    latest_val = fed.iloc[-1]
    latest_date = fed.index[-1]
    quarter = f"{latest_date.year}-Q{(latest_date.month - 1) // 3 + 1}"

    # YoY change
    latest_period = latest_date.to_period('Q')
    target_period = latest_period - 4
    yoy_matches = fed[fed.index.to_period('Q') == target_period]
    if len(yoy_matches) > 0:
        delta = latest_val - yoy_matches.iloc[0]
        direction = "up" if delta > 0 else "down"
        yoy_bullet = f"<li>That is {direction} {abs(delta):.1f} pp from a year ago.</li>"
    else:
        yoy_bullet = ""

    # Historical peak
    peak_val = fed.max()
    peak_date = fed.idxmax()
    peak_quarter = f"{peak_date.year}-Q{(peak_date.month - 1) // 3 + 1}"

    return f"""
    <div class="key-takeaways">
        <h3>Fed Treasury Holdings</h3>
        <ul>
            <li>The Federal Reserve held {latest_val:.1f}% of publicly held federal debt as of {quarter}.</li>
            {yoy_bullet}
            <li>The historical peak was {peak_val:.1f}% in {peak_quarter}.</li>
            <li>Source: FRED series FDHBFRBN (Fed holdings) and FYGFDPUN (debt held by public).</li>
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


def build_current_account_takeaways():
    """Return a takeaway panel for the current account chart."""
    path = PROC_DIR / 'current_account_gdp.csv'
    if not path.exists():
        return ""

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')
    ca = df['ca_pct_gdp'].dropna()
    if len(ca) < 5:
        return ""

    latest_val = ca.iloc[-1]
    latest_date = ca.index[-1]
    quarter = f"{latest_date.year}-Q{(latest_date.month - 1) // 3 + 1}"

    # YoY change
    comp_val = ca.iloc[-5]
    delta = latest_val - comp_val
    direction = "up" if delta > 0 else "down"

    # Post-1990 context
    post_1990 = ca[ca.index >= '1990-01-01']
    neg_pct = (post_1990 < 0).mean() * 100

    return f"""
    <div class="key-takeaways">
        <h3>Current Account</h3>
        <ul>
            <li>The U.S. current account balance was {latest_val:.1f}% of GDP as of {quarter}.</li>
            <li>That is {direction} {abs(delta):.1f} pp from a year ago.</li>
            <li>The U.S. has run a current account deficit in {neg_pct:.0f}% of quarters since 1990, reflecting its role as supplier of the world's primary reserve asset.</li>
            <li>Source: FRED series NETFI (current account) and GDP.</li>
        </ul>
    </div>"""


def build_debt_to_gdp_takeaways():
    """Return a takeaway panel for the debt-to-GDP chart."""
    path = PROC_DIR / 'debt_to_gdp.csv'
    if not path.exists():
        return ""

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')
    dtg = df['debt_gdp'].dropna()
    if len(dtg) < 5:
        return ""

    latest_val = dtg.iloc[-1]
    latest_date = dtg.index[-1]
    quarter = f"{latest_date.year}-Q{(latest_date.month - 1) // 3 + 1}"

    # YoY change
    comp_val = dtg.iloc[-5]
    delta = latest_val - comp_val
    direction = "up" if delta > 0 else "down"

    # Pre-2008 vs post-2008 averages
    pre_2008 = dtg[dtg.index < '2008-01-01'].mean()
    post_2008 = dtg[dtg.index >= '2008-01-01'].mean()

    return f"""
    <div class="key-takeaways">
        <h3>Debt-to-GDP</h3>
        <ul>
            <li>U.S. federal debt stood at {latest_val:.1f}% of GDP as of {quarter}.</li>
            <li>That is {direction} {abs(delta):.1f} pp from a year ago.</li>
            <li>The average debt-to-GDP ratio rose from {pre_2008:.0f}% (pre-2008) to {post_2008:.0f}% (post-2008), accelerating after the GFC and COVID.</li>
            <li>Source: FRED series GFDEGDQ188S.</li>
        </ul>
    </div>"""


def build_deficit_takeaways():
    """Return a takeaway panel for the deficit/GDP chart."""
    path = PROC_DIR / 'deficit_gdp.csv'
    if not path.exists():
        return ""

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')
    deficit = df['deficit_gdp'].dropna()
    if len(deficit) < 2:
        return ""

    latest_val = deficit.iloc[-1]
    latest_date = deficit.index[-1]
    year_str = str(latest_date.year)

    # YoY change
    prior_val = deficit.iloc[-2]
    delta = latest_val - prior_val
    direction = "up" if delta > 0 else "down"

    # Count deficit years
    total_years = len(deficit)
    deficit_years = (deficit < 0).sum()
    deficit_pct = deficit_years / total_years * 100

    # Post-2000 average
    post_2000 = deficit[deficit.index >= '2000-01-01']
    avg_post_2000 = post_2000.mean() if len(post_2000) > 0 else 0

    return f"""
    <div class="key-takeaways">
        <h3>Federal Deficit</h3>
        <ul>
            <li>The federal surplus/deficit was {latest_val:.1f}% of GDP in {year_str}.</li>
            <li>That is {direction} {abs(delta):.1f} pp from the prior year.</li>
            <li>The U.S. has run a deficit in {deficit_pct:.0f}% of years in this dataset. The post-2000 average is {avg_post_2000:.1f}%.</li>
            <li>Source: FRED series FYFSGDA188S.</li>
        </ul>
    </div>"""


def build_r_minus_g_takeaways():
    """Return a takeaway panel for the r − g chart."""
    path = PROC_DIR / 'r_minus_g.csv'
    if not path.exists():
        return ""

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')
    rg = df['r_minus_g'].dropna()
    if len(rg) < 5:
        return ""

    latest_val = rg.iloc[-1]
    latest_date = rg.index[-1]
    quarter = f"{latest_date.year}-Q{(latest_date.month - 1) // 3 + 1}"

    # YoY change
    comp_val = rg.iloc[-5]
    delta = latest_val - comp_val
    direction = "up" if delta > 0 else "down"

    # Share of quarters with r > g
    r_gt_g_pct = (rg > 0).mean() * 100

    # Interpretation
    if latest_val > 0:
        regime = "r exceeds g, meaning debt dynamics put upward pressure on the debt-to-GDP ratio absent primary surpluses"
    else:
        regime = "g exceeds r, meaning the economy can grow its way out of debt even with moderate primary deficits"

    return f"""
    <div class="key-takeaways">
        <h3>r &minus; g</h3>
        <ul>
            <li>r &minus; g stood at {latest_val:.1f} pp as of {quarter} &mdash; {regime}.</li>
            <li>That is {direction} {abs(delta):.1f} pp from a year ago.</li>
            <li>Historically, r has exceeded g in {r_gt_g_pct:.0f}% of quarters in this dataset.</li>
            <li>Source: FRED DGS10 (10-year yield) minus nominal GDP growth (FRED GDP).</li>
        </ul>
    </div>"""


