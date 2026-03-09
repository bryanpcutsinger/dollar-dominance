"""
Qualitative/editorial content and methodology for the Dollar Dominance Dashboard.

Separates hard-coded editorial data from data-driven chart code.
All content includes source citations.
"""


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

<p><strong>Dollar Index (DTWEXBGS):</strong> Nominal Broad U.S. Dollar Index from
the Federal Reserve, trade-weighted against a broad set of currencies.</p>
"""
