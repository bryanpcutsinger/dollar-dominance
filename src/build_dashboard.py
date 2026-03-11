"""
Build the Dollar Dominance Dashboard as a single self-contained HTML file.

Orchestrator: calls chart/component/qualitative builders and assembles
them into a tabbed HTML layout with a sticky header.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.build_charts import (
    build_chart_cofer,
    build_chart_debt_securities,
    build_chart_dxy,
    build_chart_fx_turnover,
    build_chart_treasuries,
)
from src.build_components import (
    build_cofer_takeaways,
    build_debt_takeaways,
    build_dxy_takeaways,
    build_fx_takeaways,
    build_key_takeaways,
    build_metric_cards,
    build_sticky_header,
    build_treasuries_takeaways,
)
from src.qualitative_data import authors_html, methodology_html

PROC_DIR = Path('data/processed')
OUTPUT_DIR = Path('output')


def build_dashboard():
    """Generate the complete dashboard HTML file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load metadata for last-updated date
    meta_path = PROC_DIR / 'metadata.json'
    last_updated = datetime.now().strftime('%Y-%m-%d')
    if meta_path.exists():
        with open(meta_path) as f:
            meta = json.load(f)
            last_updated = meta.get('last_updated', last_updated)[:10]

    print("  Building charts...")
    chart_cofer = build_chart_cofer(event_markers=False)
    chart_fx = build_chart_fx_turnover()
    chart_debt = build_chart_debt_securities()
    chart_treasuries = build_chart_treasuries(event_markers=False)
    chart_dxy = build_chart_dxy(event_markers=False)

    # Components
    print("  Building components...")
    metric_cards = build_metric_cards()
    key_takeaways = build_key_takeaways()
    sticky_header = build_sticky_header()
    cofer_takeaways = build_cofer_takeaways()
    fx_takeaways = build_fx_takeaways()
    debt_takeaways = build_debt_takeaways()
    treasuries_takeaways = build_treasuries_takeaways()
    dxy_takeaways = build_dxy_takeaways()
    # Qualitative / editorial
    print("  Building qualitative sections...")
    methodology = methodology_html()
    authors = authors_html()

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dollar Dominance Dashboard</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><text x='50%25' y='50%25' dominant-baseline='central' text-anchor='middle' font-size='56' font-weight='900' fill='%232e7d32' font-family='Arial,sans-serif'>$</text></svg>">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Serif+4:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
    <style>
        * {{ box-sizing: border-box; }}
        :root {{
            --color-primary: #0f5499;
            --color-bg: #f2f2f0;
            --color-text: #1a1a2e;
            --color-text-secondary: #5a5a7a;
            --color-text-muted: #737385;
            --color-border: #e2e0dc;
            --color-card-bg: #ffffff;
            --color-takeaway-bg: #fafaf8;
            --color-delta-up: #0a7a3f;
            --color-delta-down: #c22a2a;
            --font-body: 'Inter', -apple-system, system-ui, sans-serif;
            --font-heading: 'Source Serif 4', Georgia, serif;
        }}
        body {{
            font-family: var(--font-body);
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px 32px;
            background: var(--color-bg);
            color: var(--color-text);
        }}
        h1 {{
            font-family: var(--font-heading);
            font-size: 32px;
            font-weight: 700;
            color: var(--color-text);
            letter-spacing: -0.5px;
            margin-bottom: 4px;
        }}
        .subtitle {{
            color: var(--color-text-secondary);
            font-size: 15px;
            line-height: 1.5;
            margin-bottom: 20px;
        }}
        .meta-line {{
            font-size: 12px;
            color: var(--color-text-muted);
            margin-top: 8px;
        }}

        /* ── Sticky Header ── */
        .sticky-header {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border-bottom: 1px solid var(--color-border);
            padding: 8px 0;
            pointer-events: none;
        }}
        .sticky-inner {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            align-items: center;
            gap: 16px;
            font-size: 13px;
        }}
        .sticky-title {{
            font-weight: 700;
            color: var(--color-text);
            margin-right: 8px;
        }}
        .sticky-item {{ display: inline-flex; align-items: center; gap: 4px; }}
        .sticky-label {{ color: var(--color-text-secondary); }}
        .sticky-value {{ font-weight: 600; color: var(--color-primary); }}
        .sticky-sep {{ color: var(--color-border); }}

        /* ── Tab Navigation ── */
        .tab-bar {{
            display: flex;
            gap: 0;
            border-bottom: 1px solid var(--color-border);
            margin-bottom: 28px;
        }}
        .tab-btn {{
            padding: 12px 24px;
            border: none;
            background: none;
            font-size: 14px;
            font-weight: 500;
            color: var(--color-text-muted);
            cursor: pointer;
            border-bottom: 2px solid transparent;
            margin-bottom: -1px;
            transition: color 0.2s, border-color 0.2s;
            font-family: inherit;
            letter-spacing: 0.3px;
        }}
        .tab-btn:hover {{ color: var(--color-text); }}
        .tab-btn:focus-visible {{ outline: 2px solid var(--color-primary); outline-offset: -2px; }}
        .tab-btn.active {{
            color: var(--color-primary);
            font-weight: 600;
            border-bottom-color: var(--color-primary);
        }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}

        /* ── Two-Column Layout ── */
        .two-col-layout {{
            display: grid;
            grid-template-columns: 1fr 360px;
            gap: 28px;
            align-items: start;
        }}
        .two-col-right {{
            position: sticky;
            top: 80px;
            align-self: start;
            max-height: calc(100vh - 100px);
            overflow-y: auto;
        }}

        /* ── Section Labels ── */
        .section-label {{
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-family: var(--font-body);
            font-weight: 600;
            color: var(--color-text-muted);
            margin-bottom: 8px;
        }}

        /* ── Category Badges ── */
        .category-badge {{
            display: inline-block;
            font-size: 9px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 2px 8px;
            border-radius: 3px;
            margin-bottom: 8px;
        }}
        .badge-reserve {{ background: #e8f0fa; color: #0f5499; }}
        .badge-trade {{ background: #fef3e0; color: #b07800; }}
        .badge-finance {{ background: #f0ebf5; color: #5b3e8a; }}
        .badge-demand {{ background: #e5f2f0; color: #0a6a5a; }}
        .badge-index {{ background: #eaf2e5; color: #3a6e1e; }}

        .metric-cards-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }}
        .metric-card {{
            background: var(--color-card-bg);
            border-radius: 10px;
            padding: 24px;
            border: 1px solid var(--color-border);
            border-left: 3px solid transparent;
            box-shadow: none;
        }}
        .card-label {{
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            color: var(--color-text-secondary);
            margin-bottom: 4px;
        }}
        .card-value {{
            font-size: 32px;
            font-weight: 700;
            color: var(--color-text);
            margin-bottom: 4px;
            font-feature-settings: 'tnum';
            line-height: 1.1;
        }}
        .card-delta {{ font-size: 13px; margin-bottom: 4px; }}
        .card-date {{ font-size: 11px; color: var(--color-text-muted); }}
        .card-footnote {{ font-size: 10px; color: var(--color-text-muted); margin-top: 6px; font-style: italic; }}

        /* ── Trends Table ── */
        .trends-table-container {{
            background: var(--color-card-bg);
            border-radius: 10px;
            padding: 24px;
            margin-bottom: 24px;
            border: 1px solid var(--color-border);
            box-shadow: none;
        }}
        .trends-table-container h3 {{
            margin-top: 0;
            font-size: 16px;
            color: var(--color-text);
        }}
        .trends-table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        .trends-table th {{ background: #f5f3f0; text-align: left; padding: 10px; border-bottom: 2px solid var(--color-border); }}
        .trends-table td {{ padding: 10px; border-bottom: 1px solid #eee; }}

        /* ── Key Takeaways ── */
        .key-takeaways {{
            background: var(--color-takeaway-bg);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 24px;
            border: 1px solid var(--color-border);
            box-shadow: none;
        }}
        .key-takeaways h3 {{
            margin-top: 0;
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--color-primary);
            font-family: var(--font-body);
        }}
        .key-takeaways ul {{
            margin: 0;
            padding-left: 18px;
            line-height: 1.75;
            font-size: 14px;
            font-family: var(--font-heading);
            color: #3a3a4a;
        }}
        .key-takeaways li {{ margin-bottom: 6px; }}
        .key-takeaways li::marker {{ color: var(--color-primary); }}

        /* ── Chart containers ── */
        .chart-container {{
            background: var(--color-card-bg);
            border-radius: 10px;
            padding: 24px 28px;
            padding-bottom: 30px;
            margin-bottom: 24px;
            border: 1px solid var(--color-border);
            box-shadow: none;
        }}
        .section-header {{
            font-size: 15px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--color-text-secondary);
            border-bottom: 1px solid var(--color-border);
            padding-bottom: 8px;
            margin: 32px 0 16px 0;
        }}

        /* ── Summary Table ── */
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th {{ background: #f5f3f0; text-align: left; padding: 10px; border-bottom: 2px solid var(--color-border); }}
        td {{ padding: 10px; border-bottom: 1px solid #eee; }}
        .source-note {{ font-size: 12px; color: var(--color-text-secondary); margin-top: 8px; }}

        /* ── Methodology ── */
        .methodology {{
            background: var(--color-card-bg);
            border-radius: 10px;
            padding: 24px;
            font-size: 14px;
            line-height: 1.7;
        }}

        /* ── Citation Block ── */
        .citation-block {{
            margin-top: 32px;
            padding: 20px 24px;
            background: var(--color-bg);
            border-left: 3px solid var(--color-primary);
            border-radius: 4px;
        }}
        .citation-block h4 {{
            margin: 0 0 8px 0;
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--color-primary);
        }}
        .citation-block p {{
            margin: 0;
            font-size: 13px;
            line-height: 1.6;
            color: #3a3a4a;
            font-family: var(--font-heading);
        }}

        /* ── Authors ── */
        .authors-section {{ margin-top: 32px; padding-top: 24px; border-top: 1px solid var(--color-border); }}
        .authors-section h3 {{ margin-top: 0; font-size: 16px; color: var(--color-text); }}
        .authors-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; margin-top: 16px; }}
        .author-card {{ display: flex; gap: 16px; align-items: flex-start; }}
        .author-photo {{ width: 96px; height: 96px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }}
        .author-info h4 {{ margin: 0 0 6px 0; font-size: 15px; color: var(--color-text); }}
        .author-info p {{ margin: 0; font-size: 13px; line-height: 1.6; color: var(--color-text-secondary); }}

        html {{ scroll-behavior: smooth; }}

        /* ── Sticky Header Transition ── */
        .sticky-header {{
            opacity: 0;
            transform: translateY(-100%);
            transition: opacity 0.2s, transform 0.2s;
        }}
        .sticky-header.visible {{
            opacity: 1;
            transform: translateY(0);
            pointer-events: auto;
        }}

        /* ── Summary Details ── */
        details.summary-details {{
            background: var(--color-card-bg);
            border-radius: 10px;
            padding: 24px;
            padding-bottom: 30px;
            margin-bottom: 24px;
            border: 1px solid var(--color-border);
            box-shadow: none;
        }}
        details.summary-details summary {{
            font-size: 15px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--color-text-secondary);
            cursor: pointer;
            list-style: revert;
        }}

        /* ── Footer ── */
        .dashboard-footer {{
            text-align: center;
            padding: 40px 0 20px;
            border-top: 1px solid var(--color-border);
            margin-top: 48px;
        }}
        .footer-title {{
            font-family: var(--font-heading);
            font-size: 16px;
            font-weight: 600;
            color: var(--color-text);
            margin: 0 0 4px 0;
        }}
        .footer-meta {{
            font-size: 12px;
            color: var(--color-text-muted);
            margin: 0 0 12px 0;
        }}
        .footer-citation {{
            font-size: 12px;
            color: var(--color-text-secondary);
            font-family: var(--font-heading);
            line-height: 1.5;
            margin: 0;
        }}

        /* ── Responsive ── */
        @media (max-width: 768px) {{
            body {{ padding: 16px; }}
            h1 {{ font-size: 26px; }}
            .card-value {{ font-size: 26px; }}
            .two-col-layout {{
                grid-template-columns: 1fr;
            }}
            .two-col-right {{
                position: static;
                max-height: none;
                overflow-y: visible;
            }}
            .metric-cards-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            .tab-btn {{
                padding: 8px 12px;
                font-size: 13px;
            }}
            .author-card {{ flex-direction: column; align-items: center; text-align: center; }}
        }}
        @media (max-width: 480px) {{
            body {{ padding: 12px; }}
            h1 {{ font-size: 22px; }}
            .card-value {{ font-size: 24px; }}
            .tab-bar {{
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
            }}
            .tab-btn {{
                white-space: nowrap;
                flex-shrink: 0;
            }}
            .metric-cards-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        /* ── Print ── */
        @media print {{
            .sticky-header {{ display: none !important; }}
            .tab-bar {{ display: none; }}
            .tab-content {{ display: block !important; }}
            .two-col-layout {{ grid-template-columns: 1fr; }}
            .two-col-right {{ position: static; max-height: none; overflow-y: visible; }}
            .chart-container, .metric-card {{ box-shadow: none; break-inside: avoid; }}
            body {{ background: white; }}
        }}
    </style>
</head>
<body>
    {sticky_header}

    <header style="margin-bottom: 32px; padding-bottom: 24px; border-bottom: 1px solid #e2e0dc;">
        <h1>Dollar Dominance Dashboard</h1>
        <p class="subtitle">Tracking the international role of the U.S. dollar across reserves, transactions, debt, safe assets, and exchange rates</p>
        <p class="meta-line">Last updated: {last_updated} &bull; <a href="#methodology" onclick="switchTab('methodology'); return false;" style="color: #0f5499; text-decoration: none; border-bottom: 1px solid #0f549940;">Methodology &amp; Sources</a></p>
    </header>

    <!-- Tab Bar -->
    <div class="tab-bar" role="tablist" aria-label="Dashboard sections">
        <button class="tab-btn active" role="tab" aria-selected="true" data-tab="snapshot" tabindex="0" id="btn-snapshot" aria-controls="tab-snapshot">Snapshot</button>
        <button class="tab-btn" role="tab" aria-selected="false" data-tab="trends" tabindex="-1" id="btn-trends" aria-controls="tab-trends">Trends</button>
        <button class="tab-btn" role="tab" aria-selected="false" data-tab="methodology" tabindex="-1" id="btn-methodology" aria-controls="tab-methodology">Methodology</button>
    </div>

    <!-- ═══ Snapshot Tab ═══ -->
    <div id="tab-snapshot" class="tab-content active" role="tabpanel" aria-labelledby="btn-snapshot">
        <div class="section-label">Current Snapshot</div>
        <div class="two-col-layout">
            <div class="two-col-left">
                {metric_cards}
            </div>
            <div class="two-col-right">
                {key_takeaways}
            </div>
        </div>
    </div>

    <!-- ═══ Trends Tab ═══ -->
    <div id="tab-trends" class="tab-content" role="tabpanel" aria-labelledby="btn-trends">
        <div class="two-col-layout">
            <div class="two-col-left">
                <div class="chart-container" aria-label="COFER reserves stacked area chart">
                    {chart_cofer}
                </div>
            </div>
            <div class="two-col-right">
                {cofer_takeaways}
            </div>
        </div>

        <div class="two-col-layout">
            <div class="two-col-left">
                <div class="chart-container" aria-label="FX turnover grouped bar chart">
                    {chart_fx}
                </div>
            </div>
            <div class="two-col-right">
                {fx_takeaways}
            </div>
        </div>

        <div class="two-col-layout">
            <div class="two-col-left">
                <div class="chart-container" aria-label="Debt securities stacked area chart">
                    {chart_debt}
                </div>
            </div>
            <div class="two-col-right">
                {debt_takeaways}
            </div>
        </div>

        <div class="two-col-layout">
            <div class="two-col-left">
                <div class="chart-container" aria-label="Foreign Treasury holdings line chart">
                    {chart_treasuries}
                </div>
            </div>
            <div class="two-col-right">
                {treasuries_takeaways}
            </div>
        </div>

        <div class="two-col-layout">
            <div class="two-col-left">
                <div class="chart-container" aria-label="Dollar index line chart">
                    {chart_dxy}
                </div>
            </div>
            <div class="two-col-right">
                {dxy_takeaways}
            </div>
        </div>

    </div>

    <!-- ═══ Methodology Tab ═══ -->
    <div id="tab-methodology" class="tab-content" role="tabpanel" aria-labelledby="btn-methodology">
        <div class="methodology">
            <h3>Methodology &amp; Sources</h3>
            {methodology}
            {authors}
        </div>
    </div>

    <footer class="dashboard-footer">
        <p class="footer-title">Dollar Dominance Dashboard</p>
        <p class="footer-meta">Data last updated: {last_updated} &bull; Built with Python, Plotly, and public data from the IMF, BIS, and FRED</p>
        <p class="footer-citation">Cutsinger, Bryan, and Joshua Hendrickson. "Dollar Dominance Dashboard." American Institute for Economic Research, Sound Money Project. <a href="https://bryanpcutsinger.github.io/dollar-dominance/" style="color:#0f5499;">bryanpcutsinger.github.io/dollar-dominance</a>.</p>
    </footer>

    <script>
        // Tab switching via data-tab attributes
        function switchTab(name) {{
            // Hide all tabs, deactivate all buttons
            document.querySelectorAll('.tab-content').forEach(function(el) {{
                el.classList.remove('active');
            }});
            document.querySelectorAll('.tab-btn').forEach(function(btn) {{
                btn.classList.remove('active');
                btn.setAttribute('aria-selected', 'false');
                btn.setAttribute('tabindex', '-1');
            }});

            // Show selected tab
            var tab = document.getElementById('tab-' + name);
            if (tab) {{
                tab.classList.add('active');
            }}

            // Activate matching button via data-tab attribute
            var activeBtn = document.querySelector('.tab-btn[data-tab="' + name + '"]');
            if (activeBtn) {{
                activeBtn.classList.add('active');
                activeBtn.setAttribute('aria-selected', 'true');
                activeBtn.setAttribute('tabindex', '0');
                activeBtn.focus();
            }}

            // Update URL hash without polluting history
            history.replaceState(null, '', '#' + name);

            // Resize Plotly charts in newly visible tab
            setTimeout(function() {{
                if (tab) {{
                    tab.querySelectorAll('.js-plotly-plot').forEach(function(plot) {{
                        Plotly.Plots.resize(plot);
                    }});
                }}
            }}, 50);
        }}

        // Tab button click handlers via delegation
        document.querySelector('.tab-bar').addEventListener('click', function(e) {{
            var btn = e.target.closest('.tab-btn');
            if (btn && btn.dataset.tab) {{
                switchTab(btn.dataset.tab);
            }}
        }});

        // Keyboard navigation for tabs (arrow keys)
        document.querySelector('.tab-bar').addEventListener('keydown', function(e) {{
            var tabs = Array.from(document.querySelectorAll('.tab-btn'));
            var current = document.activeElement;
            var idx = tabs.indexOf(current);
            if (idx === -1) return;

            var newIdx = -1;
            if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {{
                newIdx = (idx + 1) % tabs.length;
            }} else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {{
                newIdx = (idx - 1 + tabs.length) % tabs.length;
            }} else if (e.key === 'Home') {{
                newIdx = 0;
            }} else if (e.key === 'End') {{
                newIdx = tabs.length - 1;
            }}

            if (newIdx !== -1) {{
                e.preventDefault();
                switchTab(tabs[newIdx].dataset.tab);
            }}
        }});

        // Hash routing: open tab from URL hash on load and hashchange
        function openTabFromHash() {{
            var hash = location.hash.replace('#', '');
            var validTabs = ['snapshot', 'trends', 'methodology'];
            if (hash && validTabs.indexOf(hash) !== -1) {{
                switchTab(hash);
            }}
        }}
        document.addEventListener('DOMContentLoaded', openTabFromHash);
        window.addEventListener('hashchange', openTabFromHash);

        // Sticky header: smooth fade in/out on scroll > 200px
        window.addEventListener('scroll', function() {{
            var header = document.getElementById('sticky-header');
            if (header) {{
                if (window.scrollY > 200) {{
                    header.classList.add('visible');
                }} else {{
                    header.classList.remove('visible');
                }}
            }}
        }});

        // Auto-resize Plotly charts on window resize
        window.addEventListener('resize', function() {{
            document.querySelectorAll('.js-plotly-plot').forEach(function(plot) {{
                Plotly.Plots.resize(plot);
            }});
        }});
    </script>
</body>
</html>"""

    outpath = OUTPUT_DIR / 'index.html'
    with open(outpath, 'w') as f:
        f.write(html)

    file_size = outpath.stat().st_size
    size_mb = file_size / (1024 * 1024)
    print(f"  Dashboard saved to {outpath} ({size_mb:.1f} MB)")
    if size_mb > 10:
        print(f"  WARNING: File size exceeds 10MB. Consider optimizing chart data.")

    return outpath


if __name__ == '__main__':
    build_dashboard()
