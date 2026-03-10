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
from src.qualitative_data import methodology_html

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

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dollar Dominance Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #fafafa;
            color: #333;
        }}
        h1 {{ font-size: 28px; margin-bottom: 4px; }}
        .subtitle {{ color: #666; font-size: 14px; margin-bottom: 20px; }}

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
            border-bottom: 1px solid #e0e0e0;
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
            color: #333;
            margin-right: 8px;
        }}
        .sticky-item {{ display: inline-flex; align-items: center; gap: 4px; }}
        .sticky-label {{ color: #666; }}
        .sticky-value {{ font-weight: 600; color: #1f77b4; }}
        .sticky-sep {{ color: #ddd; }}

        /* ── Tab Navigation ── */
        .tab-bar {{
            display: flex;
            gap: 0;
            border-bottom: 2px solid #e0e0e0;
            margin-bottom: 24px;
        }}
        .tab-btn {{
            padding: 10px 20px;
            border: none;
            background: none;
            font-size: 14px;
            font-weight: 500;
            color: #888;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            margin-bottom: -2px;
            transition: color 0.2s, border-color 0.2s;
            font-family: inherit;
        }}
        .tab-btn:hover {{ color: #555; }}
        .tab-btn:focus-visible {{ outline: 2px solid #1f77b4; outline-offset: -2px; }}
        .tab-btn.active {{
            color: #1f77b4;
            border-bottom-color: #1f77b4;
        }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}

        /* ── Metric Cards ── */
        /* ── Two-Column Layout ── */
        .two-col-layout {{
            display: grid;
            grid-template-columns: 1fr 380px;
            gap: 20px;
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
            font-size: 9px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
            color: #888;
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
        .badge-reserve {{ background: #e3f2fd; color: #1565c0; }}
        .badge-trade {{ background: #fff3e0; color: #e65100; }}
        .badge-finance {{ background: #f3e5f5; color: #7b1fa2; }}
        .badge-demand {{ background: #e0f2f1; color: #00695c; }}
        .badge-index {{ background: #e8f5e9; color: #2e7d32; }}

        .metric-cards-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .metric-card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .card-label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #666;
            margin-bottom: 4px;
        }}
        .card-value {{
            font-size: 28px;
            font-weight: 700;
            color: #1f77b4;
            margin-bottom: 4px;
        }}
        .card-delta {{ font-size: 13px; margin-bottom: 4px; }}
        .card-date {{ font-size: 11px; color: #717171; }}
        .card-footnote {{ font-size: 10px; color: #717171; margin-top: 6px; font-style: italic; }}

        /* ── Trends Table ── */
        .trends-table-container {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .trends-table-container h3 {{
            margin-top: 0;
            font-size: 16px;
            color: #333;
        }}
        .trends-table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        .trends-table th {{ background: #f5f5f5; text-align: left; padding: 10px; border-bottom: 2px solid #ddd; }}
        .trends-table td {{ padding: 10px; border-bottom: 1px solid #eee; }}

        /* ── Key Takeaways ── */
        .key-takeaways {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .key-takeaways h3 {{
            margin-top: 0;
            font-size: 16px;
            color: #333;
        }}
        .key-takeaways ul {{
            margin: 0;
            padding-left: 20px;
            line-height: 1.8;
            font-size: 14px;
        }}

        /* ── Chart containers ── */
        .chart-container {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            padding-bottom: 30px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .section-header {{
            font-size: 15px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #666;
            border-bottom: 2px solid #eee;
            padding-bottom: 8px;
            margin: 24px 0 12px 0;
        }}

        /* ── Summary Table ── */
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th {{ background: #f5f5f5; text-align: left; padding: 10px; border-bottom: 2px solid #ddd; }}
        td {{ padding: 10px; border-bottom: 1px solid #eee; }}
        .source-note {{ font-size: 12px; color: #666; margin-top: 8px; }}

        /* ── Methodology ── */
        .methodology {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            font-size: 13px;
            line-height: 1.6;
        }}

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
            background: white;
            border-radius: 8px;
            padding: 20px;
            padding-bottom: 30px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        details.summary-details summary {{
            font-size: 15px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #666;
            cursor: pointer;
            list-style: revert;
        }}

        /* ── Responsive ── */
        @media (max-width: 768px) {{
            .two-col-layout {{
                grid-template-columns: 1fr;
            }}
            .two-col-right {{
                position: static;
                max-height: none;
                overflow-y: visible;
            }}
            .metric-cards-grid {{
                grid-template-columns: 1fr;
            }}
            .tab-btn {{
                padding: 8px 12px;
                font-size: 13px;
            }}
        }}
        @media (max-width: 480px) {{
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

    <h1>Dollar Dominance Dashboard</h1>
    <p class="subtitle">
        Tracking the international role of the U.S. dollar across reserves, transactions, debt, safe assets, and exchange rates<br>
        Last updated: {last_updated}
    </p>

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
        </div>
    </div>

    <footer style="text-align:center;padding:40px 0 20px;font-size:12px;color:#717171;">
        Dollar Dominance Dashboard &mdash; Last updated: {last_updated}
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
