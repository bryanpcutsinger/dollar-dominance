"""
Qualitative/editorial content and methodology for the Dollar Dominance Dashboard.

Separates hard-coded editorial data from data-driven chart code.
All content includes source citations.
"""

import base64
import io
from pathlib import Path

# Author bios keyed by filename stem
AUTHOR_BIOS = {
    "Bryan Cutsinger": (
        "Bryan Cutsinger is an Assistant Professor of Economics at Florida Atlantic "
        "University and a fellow with the Sound Money Project at the American Institute "
        "for Economic Research. His research focuses on monetary theory and history, with "
        "emphasis on the institutional foundations of monetary systems and the political "
        "economy of central banking. He serves as Associate Editor of <em>Public Choice</em> "
        "and Director of Undergraduate Studies at FAU."
    ),
    "Joshua Hendrickson": (
        "Joshua Hendrickson is Professor and Chair of the Department of Economics at the "
        "University of Mississippi. He is a Senior Fellow with the Sound Money Project at "
        "the American Institute for Economic Research and a Senior Affiliate Scholar at the "
        "Mercatus Center at George Mason University. His research focuses on monetary theory "
        "and political economy, with recent work on nominal GDP targeting and the political "
        "economy of Bitcoin."
    ),
}


def authors_html(bios_dir: Path = Path('bios')) -> str:
    """Return HTML for the Authors section with embedded headshot thumbnails."""
    try:
        from PIL import Image
    except ImportError:
        print("  WARNING: Pillow not installed — skipping author photos")
        Image = None

    cards = []
    for name, bio in AUTHOR_BIOS.items():
        # Try to find a headshot image (png, jpg, jpeg)
        photo_html = ""
        for ext in ('png', 'jpg', 'jpeg'):
            img_path = bios_dir / f"{name}.{ext}"
            if img_path.exists():
                if Image is not None:
                    img = Image.open(img_path)
                    img.thumbnail((300, 300))
                    buf = io.BytesIO()
                    # Convert to RGB if needed (e.g. PNG with alpha)
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    img.save(buf, format='JPEG', quality=80)
                    b64 = base64.b64encode(buf.getvalue()).decode()
                    photo_html = f'<img class="author-photo" src="data:image/jpeg;base64,{b64}" alt="{name}">'
                else:
                    # Fallback: embed raw file (no resize)
                    raw = img_path.read_bytes()
                    mime = 'image/png' if ext == 'png' else 'image/jpeg'
                    b64 = base64.b64encode(raw).decode()
                    photo_html = f'<img class="author-photo" src="data:{mime};base64,{b64}" alt="{name}">'
                break

        cards.append(f"""
        <div class="author-card">
            {photo_html}
            <div class="author-info">
                <h4>{name}</h4>
                <p>{bio}</p>
            </div>
        </div>""")

    return f"""
    <div class="authors-section">
        <h3>Authors</h3>
        <div class="authors-grid">
            {''.join(cards)}
        </div>
    </div>"""


def methodology_html():
    """Return the methodology section HTML."""
    return """
<p><strong>FX Reserves (COFER):</strong> Quarterly data from the IMF Currency
Composition of Official Foreign Exchange Reserves survey. 149 reporting economies.
Starting 2025Q3, the IMF eliminated the "unallocated" category and now provides
complete currency composition for 100% of global reserves. Prior to 2025Q3, shares
reflect allocated reserves only (~90% of total). Exchange rate valuation effects
can significantly distort quarter-to-quarter changes in currency shares &mdash; a
large DXY decline mechanically reduces the USD share even if no central bank
changes its portfolio.</p>

<p><strong>FX Turnover (BIS Triennial):</strong> Conducted every three years in April.
Shares sum to 200% because two currencies are involved in each transaction. Data
from 52 jurisdictions covering 1,100+ dealers.</p>

<p><strong>Debt Securities (BIS):</strong> Currency denomination of international
debt securities outstanding. Quarterly. Includes all issuers and all maturities.
Note: Only USD, EUR, and Other breakdown is available from the BIS bulk dataset
at the aggregate level.</p>

<p><strong>Foreign Holdings of Treasuries (FRED):</strong> Quarterly data from the
U.S. Treasury via FRED. Foreign holdings (FDHBFIN, billions) divided by total public
debt (GFDEBTN, millions) gives the share of U.S. federal debt held by foreign and
international investors. Unlike the BIS debt securities measure (which tracks currency
denomination of international bonds), this captures foreign demand for U.S. sovereign
debt specifically &mdash; a proxy for confidence in dollar-denominated safe assets.
FDHBFIN typically lags one quarter behind GFDEBTN. Available since 1970.</p>

<p><strong>Dollar Index (DTWEXBGS):</strong> Nominal Broad U.S. Dollar Index from
the Federal Reserve, trade-weighted against a broad set of currencies.</p>

<div class="citation-block">
    <h4>How to Cite</h4>
    <p>Cutsinger, Bryan, and Joshua Hendrickson. "Dollar Dominance Dashboard."
    American Institute for Economic Research, Sound Money Project.
    Available at <a href="https://bryanpcutsinger.github.io/dollar-dominance/" style="color:#0f5499;">bryanpcutsinger.github.io/dollar-dominance</a>.
    Accessed [date].</p>
</div>
"""
