"""
Chart-building functions for the Dollar Dominance Dashboard.

Each function reads from data/processed/ and returns a Plotly HTML fragment
(or placeholder string) for embedding in the dashboard.
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import COLORS, EVENTS

PROC_DIR = Path('data/processed')

# Plotly layout defaults
LAYOUT_DEFAULTS = dict(
    template='plotly_white',
    font=dict(family='Inter, -apple-system, system-ui, sans-serif', size=12, color='#5a5a7a'),
    margin=dict(l=50, r=40, t=60, b=80),
    hovermode='x unified',
    plot_bgcolor='white',
    paper_bgcolor='white',
    hoverlabel=dict(bgcolor='white', font_size=12, font_family='Inter, sans-serif', bordercolor='#e2e0dc'),
)

PLOTLY_CONFIG = {'displayModeBar': True, 'displaylogo': False}


def _placeholder(message):
    """Return a placeholder div for missing data."""
    return f'<div style="padding:40px;text-align:center;color:#737385;font-style:italic;">{message}</div>'


def _add_event_markers(fig, events=None, y_range=None):
    """Add vertical dashed lines for key events using shapes + annotations."""
    if events is None:
        events = EVENTS
    for date_str, label in events.items():
        if label == 'COFER methodology change':
            continue  # handled separately in COFER chart
        fig.add_shape(
            type="line", x0=date_str, x1=date_str, y0=0, y1=1,
            yref="paper", line=dict(color="#d4d2ce", width=1, dash="dot"),
        )
        fig.add_annotation(
            x=date_str, y=1, yref="paper",
            text=label, showarrow=False,
            font=dict(size=10, color="#737385"),
            yshift=10,
        )


def build_chart_cofer(event_markers=True):
    """Chart 1: COFER Reserves stacked area chart."""
    path = PROC_DIR / 'cofer_shares.csv'
    if not path.exists():
        return _placeholder("COFER reserves data unavailable.")

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')

    # Stack order (bottom to top): USD, EUR, JPY, GBP, CNY, CHF, AUD, CAD, Other
    stack_order = ['usd', 'eur', 'jpy', 'gbp', 'cny', 'chf', 'aud', 'cad', 'other']
    labels = {'usd': 'USD', 'eur': 'EUR', 'jpy': 'JPY', 'gbp': 'GBP',
              'cny': 'CNY', 'chf': 'CHF', 'aud': 'AUD', 'cad': 'CAD', 'other': 'Other'}

    fig = go.Figure()

    for col in stack_order:
        if col not in df.columns:
            continue
        fig.add_trace(go.Scatter(
            x=df.index, y=df[col],
            name=labels.get(col, col.upper()),
            mode='lines',
            stackgroup='one',
            line=dict(width=0.5),
            fillcolor=COLORS.get(col.upper(), '#999'),
            line_color=COLORS.get(col.upper(), '#999'),
        ))

    # Latest USD value annotation
    latest_usd = df['usd'].dropna().iloc[-1]
    latest_date = df['usd'].dropna().index[-1]
    quarter = f"{latest_date.year}-Q{(latest_date.month - 1) // 3 + 1}"

    fig.add_annotation(
        x=latest_date, y=latest_usd / 2,
        text=f"<b>USD: {latest_usd:.1f}%</b><br>({quarter})",
        showarrow=True, arrowhead=2, ax=60, ay=-30,
        font=dict(size=12, color=COLORS['USD']),
        bgcolor="rgba(255,255,255,0.9)", bordercolor=COLORS['USD'], borderwidth=0.5,
    )

    # Event markers
    if event_markers:
        _add_event_markers(fig)

        # COFER methodology change marker
        fig.add_shape(
            type="line", x0='2025-07-01', x1='2025-07-01', y0=0, y1=1,
            yref="paper", line=dict(color="#c22a2a", width=1, dash="dash"),
        )
        fig.add_annotation(
            x='2025-07-01', y=1, yref="paper",
            text="COFER methodology change", showarrow=False,
            font=dict(size=9, color="#c22a2a"), yshift=10,
        )

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title="Central Bank FX Reserves by Currency (IMF COFER)",
        yaxis=dict(title="Share of Reserves (%)", range=[0, 100]),
        xaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, x=0.5, xanchor="center",
                    font=dict(size=11), bgcolor='rgba(0,0,0,0)'),
    )

    return fig.to_html(full_html=False, include_plotlyjs=False, config=PLOTLY_CONFIG)


def build_chart_fx_turnover():
    """Chart 2: FX Turnover grouped bar chart."""
    path = PROC_DIR / 'fx_turnover_triennial.csv'
    if not path.exists():
        return _placeholder("FX turnover data unavailable.")

    df = pd.read_csv(path)

    currencies = ['usd', 'eur', 'jpy', 'gbp', 'cny']
    labels = {'usd': 'USD', 'eur': 'EUR', 'jpy': 'JPY', 'gbp': 'GBP', 'cny': 'CNY'}

    fig = go.Figure()

    for cur in currencies:
        fig.add_trace(go.Bar(
            x=df['year'].astype(str),
            y=df[cur],
            name=labels[cur],
            marker_color=COLORS.get(cur.upper(), '#999'),
        ))

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title="FX Transaction Volume by Currency (BIS Triennial Survey)",
        barmode='group',
        yaxis=dict(title="Share of Turnover (% of 200% total)", range=[0, 100]),
        xaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, x=0.5, xanchor="center",
                    font=dict(size=11), bgcolor='rgba(0,0,0,0)'),
    )

    # Add note about 200% total (below the legend)
    fig.add_annotation(
        text="Note: Shares sum to 200% as two currencies are involved in each FX transaction. Source: BIS Triennial Central Bank Survey.",
        xref="paper", yref="paper", x=0, y=-0.28, showarrow=False,
        font=dict(size=10, color="#737385"), align="left",
    )

    return fig.to_html(full_html=False, include_plotlyjs=False, config=PLOTLY_CONFIG)


def build_chart_debt_securities():
    """Chart 3: Debt Securities stacked area chart."""
    path = PROC_DIR / 'debt_securities_shares.csv'
    if not path.exists():
        return _placeholder("BIS debt securities data unavailable.")

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')

    stack_order = ['usd', 'eur', 'other']
    labels = {'usd': 'USD', 'eur': 'EUR', 'other': 'Other'}

    fig = go.Figure()

    for col in stack_order:
        if col not in df.columns:
            continue
        fig.add_trace(go.Scatter(
            x=df.index, y=df[col],
            name=labels.get(col, col.upper()),
            mode='lines',
            stackgroup='one',
            line=dict(width=0.5),
            fillcolor=COLORS.get(col.upper(), '#999'),
            line_color=COLORS.get(col.upper(), '#999'),
        ))

    # Latest USD annotation
    latest_usd = df['usd'].dropna().iloc[-1]
    latest_date = df['usd'].dropna().index[-1]
    quarter = f"{latest_date.year}-Q{(latest_date.month - 1) // 3 + 1}"

    fig.add_annotation(
        x=latest_date, y=latest_usd / 2,
        text=f"<b>USD: {latest_usd:.1f}%</b><br>({quarter})",
        showarrow=True, arrowhead=2, ax=60, ay=-30,
        font=dict(size=12, color=COLORS['USD']),
        bgcolor="rgba(255,255,255,0.9)", bordercolor=COLORS['USD'], borderwidth=0.5,
    )

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title="Currency Denomination of International Debt Securities (BIS)",
        yaxis=dict(title="Share (%)", range=[0, 100]),
        xaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, x=0.5, xanchor="center",
                    font=dict(size=11), bgcolor='rgba(0,0,0,0)'),
    )

    return fig.to_html(full_html=False, include_plotlyjs=False, config=PLOTLY_CONFIG)


def build_chart_treasuries(event_markers=True):
    """Chart: Foreign holdings of US Treasuries as share of publicly held debt."""
    path = PROC_DIR / 'treasury_foreign_share.csv'
    if not path.exists():
        return _placeholder("Foreign Treasury holdings data unavailable.")

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df['foreign_share'],
        name='Foreign Share of US Treasuries',
        line=dict(color=COLORS['Foreign'], width=2),
    ))

    if event_markers:
        _add_event_markers(fig)

    latest_val = df['foreign_share'].dropna().iloc[-1]
    latest_date = df['foreign_share'].dropna().index[-1]
    quarter = f"{latest_date.year}-Q{(latest_date.month - 1) // 3 + 1}"

    fig.add_annotation(
        x=latest_date, y=latest_val,
        text=f"<b>{latest_val:.1f}%</b><br>({quarter})",
        showarrow=True, arrowhead=2, ax=-60, ay=-30,
        font=dict(size=12, color=COLORS['Foreign']),
        bgcolor="rgba(255,255,255,0.9)", bordercolor=COLORS['Foreign'], borderwidth=0.5,
    )

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title="Foreign Holdings of U.S. Treasury Debt (FRED)",
        yaxis=dict(title="Share of Publicly Held Debt (%)", range=[0, 50]),
        xaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, x=0.5, xanchor="center",
                    font=dict(size=11), bgcolor='rgba(0,0,0,0)'),
    )

    return fig.to_html(full_html=False, include_plotlyjs=False, config=PLOTLY_CONFIG)


def build_chart_fed_holdings(event_markers=True):
    """Chart: Federal Reserve holdings of US Treasuries as share of publicly held debt."""
    path = PROC_DIR / 'treasury_fed_share.csv'
    if not path.exists():
        return _placeholder("Fed Treasury holdings data unavailable.")

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df['fed_share'],
        name='Fed Share of US Treasuries',
        line=dict(color=COLORS['Fed'], width=2),
    ))

    if event_markers:
        _add_event_markers(fig)

    fed = df['fed_share'].dropna()
    latest_val = fed.iloc[-1]
    latest_date = fed.index[-1]
    quarter = f"{latest_date.year}-Q{(latest_date.month - 1) // 3 + 1}"

    fig.add_annotation(
        x=latest_date, y=latest_val,
        text=f"<b>{latest_val:.1f}%</b><br>({quarter})",
        showarrow=True, arrowhead=2, ax=-60, ay=-30,
        font=dict(size=12, color=COLORS['Fed']),
        bgcolor="rgba(255,255,255,0.9)", bordercolor=COLORS['Fed'], borderwidth=0.5,
    )

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title="Federal Reserve Holdings of U.S. Treasury Debt (FRED)",
        yaxis=dict(title="Share of Publicly Held Debt (%)", range=[0, 35]),
        xaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, x=0.5, xanchor="center",
                    font=dict(size=11), bgcolor='rgba(0,0,0,0)'),
    )

    return fig.to_html(full_html=False, include_plotlyjs=False, config=PLOTLY_CONFIG)


def build_chart_current_account(event_markers=True):
    """Chart: U.S. current account balance as percent of GDP."""
    path = PROC_DIR / 'current_account_gdp.csv'
    if not path.exists():
        return _placeholder("Current account data unavailable.")

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df['ca_pct_gdp'],
        name='Current Account (% of GDP)',
        line=dict(color=COLORS['CurrentAccount'], width=2),
    ))

    # Zero reference line
    fig.add_hline(y=0, line_dash="dot", line_color="#d4d2ce")

    if event_markers:
        _add_event_markers(fig)

    # Latest-value annotation
    latest_val = df['ca_pct_gdp'].dropna().iloc[-1]
    latest_date = df['ca_pct_gdp'].dropna().index[-1]
    quarter = f"{latest_date.year}-Q{(latest_date.month - 1) // 3 + 1}"

    fig.add_annotation(
        x=latest_date, y=latest_val,
        text=f"<b>{latest_val:.1f}%</b><br>({quarter})",
        showarrow=True, arrowhead=2, ax=-60, ay=-30,
        font=dict(size=12, color=COLORS['CurrentAccount']),
        bgcolor="rgba(255,255,255,0.9)", bordercolor=COLORS['CurrentAccount'], borderwidth=0.5,
    )

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title="U.S. Current Account Balance (% of GDP)",
        yaxis=dict(title="Current Account (% of GDP)"),
        xaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, x=0.5, xanchor="center",
                    font=dict(size=11), bgcolor='rgba(0,0,0,0)'),
    )

    return fig.to_html(full_html=False, include_plotlyjs=False, config=PLOTLY_CONFIG)


def build_chart_debt_to_gdp(event_markers=True):
    """Chart: U.S. federal debt-to-GDP ratio."""
    path = PROC_DIR / 'debt_to_gdp.csv'
    if not path.exists():
        return _placeholder("Debt-to-GDP data unavailable.")

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df['debt_gdp'],
        name='Federal Debt (% of GDP)',
        line=dict(color=COLORS['DebtGDP'], width=2),
    ))

    if event_markers:
        _add_event_markers(fig)

    # Latest-value annotation
    latest_val = df['debt_gdp'].dropna().iloc[-1]
    latest_date = df['debt_gdp'].dropna().index[-1]
    quarter = f"{latest_date.year}-Q{(latest_date.month - 1) // 3 + 1}"

    fig.add_annotation(
        x=latest_date, y=latest_val,
        text=f"<b>{latest_val:.1f}%</b><br>({quarter})",
        showarrow=True, arrowhead=2, ax=-60, ay=-30,
        font=dict(size=12, color=COLORS['DebtGDP']),
        bgcolor="rgba(255,255,255,0.9)", bordercolor=COLORS['DebtGDP'], borderwidth=0.5,
    )

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title="U.S. Federal Debt-to-GDP Ratio (FRED)",
        yaxis=dict(title="Federal Debt (% of GDP)", rangemode="tozero"),
        xaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, x=0.5, xanchor="center",
                    font=dict(size=11), bgcolor='rgba(0,0,0,0)'),
    )

    return fig.to_html(full_html=False, include_plotlyjs=False, config=PLOTLY_CONFIG)


def build_chart_deficit(event_markers=True):
    """Chart: U.S. federal deficit as percent of GDP."""
    path = PROC_DIR / 'deficit_gdp.csv'
    if not path.exists():
        return _placeholder("Deficit/GDP data unavailable.")

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df['deficit_gdp'],
        name='Federal Surplus/Deficit (% of GDP)',
        line=dict(color=COLORS['Deficit'], width=2),
    ))

    # Zero reference line
    fig.add_hline(y=0, line_dash="dot", line_color="#d4d2ce")

    if event_markers:
        _add_event_markers(fig)

    # Latest-value annotation
    latest_val = df['deficit_gdp'].dropna().iloc[-1]
    latest_date = df['deficit_gdp'].dropna().index[-1]
    year_str = str(latest_date.year)

    fig.add_annotation(
        x=latest_date, y=latest_val,
        text=f"<b>{latest_val:.1f}%</b><br>({year_str})",
        showarrow=True, arrowhead=2, ax=-60, ay=-30,
        font=dict(size=12, color=COLORS['Deficit']),
        bgcolor="rgba(255,255,255,0.9)", bordercolor=COLORS['Deficit'], borderwidth=0.5,
    )

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title="U.S. Federal Surplus/Deficit (% of GDP)",
        yaxis=dict(title="Surplus/Deficit (% of GDP)"),
        xaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, x=0.5, xanchor="center",
                    font=dict(size=11), bgcolor='rgba(0,0,0,0)'),
    )

    return fig.to_html(full_html=False, include_plotlyjs=False, config=PLOTLY_CONFIG)


def build_chart_r_minus_g(event_markers=True):
    """Chart: r − g (10-year yield minus nominal GDP growth)."""
    path = PROC_DIR / 'r_minus_g.csv'
    if not path.exists():
        return _placeholder("r − g data unavailable.")

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df['r_minus_g'],
        name='r − g (10Y yield − nominal GDP growth)',
        line=dict(color=COLORS['RminusG'], width=2),
    ))

    # Zero reference line — r = g boundary
    fig.add_hline(y=0, line_dash="dot", line_color="#d4d2ce")

    if event_markers:
        _add_event_markers(fig)

    # Latest-value annotation
    latest_val = df['r_minus_g'].dropna().iloc[-1]
    latest_date = df['r_minus_g'].dropna().index[-1]
    quarter = f"{latest_date.year}-Q{(latest_date.month - 1) // 3 + 1}"

    fig.add_annotation(
        x=latest_date, y=latest_val,
        text=f"<b>{latest_val:.1f} pp</b><br>({quarter})",
        showarrow=True, arrowhead=2, ax=-60, ay=-30,
        font=dict(size=12, color=COLORS['RminusG']),
        bgcolor="rgba(255,255,255,0.9)", bordercolor=COLORS['RminusG'], borderwidth=0.5,
    )

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title="r − g: Interest Rate vs. Growth Rate",
        yaxis=dict(title="r − g (percentage points)"),
        xaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, x=0.5, xanchor="center",
                    font=dict(size=11), bgcolor='rgba(0,0,0,0)'),
    )

    return fig.to_html(full_html=False, include_plotlyjs=False, config=PLOTLY_CONFIG)


def build_chart_dxy(event_markers=True):
    """Standalone DXY line chart for the Trends tab."""
    path = PROC_DIR / 'dxy_weekly.csv'
    if not path.exists():
        return _placeholder("DXY data unavailable. Set FRED_API_KEY in .env and re-run pipeline.")

    dxy = pd.read_csv(path, parse_dates=['date'], index_col='date')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dxy.index, y=dxy['dxy'],
        name='Dollar Index (DXY)',
        line=dict(color=COLORS['USD'], width=2),
    ))
    if event_markers:
        _add_event_markers(fig)

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title="U.S. Dollar Index (DTWEXBGS)",
        yaxis=dict(title="Index"),
        xaxis=dict(title="", range=[dxy.index.min(), dxy.index.max()]),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, x=0.5, xanchor="center",
                    font=dict(size=11), bgcolor='rgba(0,0,0,0)'),
    )

    return fig.to_html(full_html=False, include_plotlyjs=False, config=PLOTLY_CONFIG)


