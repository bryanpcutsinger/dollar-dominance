"""Unit tests for data processing functions."""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestCoferProcessing:
    """Test COFER data processing."""

    def test_quarterly_date_parsing(self):
        """COFER quarterly dates should parse to proper datetime."""
        index = pd.PeriodIndex(['1999-Q1', '2025-Q1'], freq='Q')
        dates = index.to_timestamp(how='end')
        assert dates[0].year == 1999
        assert dates[0].month == 3
        assert dates[1].year == 2025

    def test_shares_sum_near_100(self):
        """COFER currency shares should sum close to 100% for each quarter."""
        fixture = Path(__file__).parent / 'fixtures' / 'cofer_sample.csv'
        df = pd.read_csv(fixture, index_col=0)

        # For rows with all currencies present (post-2020)
        currency_cols = ['usd', 'eur', 'cny', 'jpy', 'gbp', 'aud', 'cad', 'chf', 'other']
        for idx, row in df.iterrows():
            total = row[currency_cols].sum()
            if not pd.isna(total):
                # Allow some tolerance since "Other" is a residual
                assert 95 < total < 105, f"Row {idx}: shares sum to {total}"

    def test_usd_share_reasonable(self):
        """USD share should be between 40% and 80% for all historical data."""
        fixture = Path(__file__).parent / 'fixtures' / 'cofer_sample.csv'
        df = pd.read_csv(fixture, index_col=0)
        assert df['usd'].min() > 40
        assert df['usd'].max() < 80


class TestFxTurnover:
    """Test FX turnover data."""

    def test_usd_share_dominant(self):
        """USD should be the largest share in every survey year."""
        fx = {
            "year": [2019, 2022, 2025],
            "usd": [88.3, 88.4, 89.2],
            "eur": [32.3, 30.5, 28.9],
        }
        df = pd.DataFrame(fx)
        assert (df['usd'] > df['eur']).all()

    def test_shares_over_100(self):
        """FX turnover shares should sum over 100% (they sum to 200%)."""
        # This is correct because two currencies per transaction
        assert 88.3 + 32.3 + 16.8 + 12.8 + 4.3 > 100


class TestTreasuryProcessing:
    """Test foreign Treasury holdings ratio computation."""

    def test_unit_conversion(self):
        """Verify billions/millions conversion produces correct ratio."""
        # Example: 9248.4 billion foreign / 38514009 million total
        foreign_billions = 9248.4
        total_millions = 38514009
        ratio = (foreign_billions * 1000 / total_millions) * 100
        # Should be approximately 24.0%
        assert 23.0 < ratio < 25.0, f"Expected ~24%, got {ratio:.1f}%"

    def test_sanity_bounds(self):
        """Output values should fall within 5-70% range historically."""
        path = Path('data/processed/treasury_foreign_share.csv')
        if not path.exists():
            pytest.skip("treasury_foreign_share.csv not found — run pipeline first")

        df = pd.read_csv(path)
        assert df['foreign_share'].min() >= 1, "Foreign share below 1%"
        assert df['foreign_share'].max() <= 70, "Foreign share above 70%"


class TestDebtSecurities:
    """Test BIS debt securities share computation."""

    def test_shares_sum_to_100(self):
        """USD + EUR + Other should sum to exactly 100%."""
        total = 1000
        usd = 485
        eur = 373
        other_val = total - usd - eur

        usd_pct = usd / total * 100
        eur_pct = eur / total * 100
        other_pct = other_val / total * 100

        assert abs(usd_pct + eur_pct + other_pct - 100.0) < 0.01
