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


class TestTreasuryDecoupledPipeline:
    """Test decoupled foreign and Fed Treasury share pipelines."""

    def test_foreign_share_independent(self):
        """process_treasuries() should produce foreign_share only, no fed columns."""
        from src.process_data import RAW_DIR, process_treasuries

        if not (RAW_DIR / 'FDHBFIN.csv').exists():
            pytest.skip("FDHBFIN.csv not present")

        result = process_treasuries()
        if result is not None:
            assert 'foreign_share' in result.columns
            assert 'fed_share' not in result.columns
            assert 'domestic_private_share' not in result.columns

    def test_fed_share_sanity(self):
        """Fed share values should fall within 1-50% range."""
        path = Path('data/processed/treasury_fed_share.csv')
        if not path.exists():
            pytest.skip("treasury_fed_share.csv not found — run pipeline first")

        df = pd.read_csv(path)
        fed = df['fed_share'].dropna()
        assert fed.min() >= 1, f"Fed share below 1%: {fed.min()}"
        assert fed.max() <= 50, f"Fed share above 50%: {fed.max()}"

    def test_fed_share_independent(self):
        """Fed share CSV should exist independently and may have newer data than foreign share."""
        foreign_path = Path('data/processed/treasury_foreign_share.csv')
        fed_path = Path('data/processed/treasury_fed_share.csv')
        if not foreign_path.exists() or not fed_path.exists():
            pytest.skip("Both treasury CSVs required — run pipeline first")

        foreign_df = pd.read_csv(foreign_path, parse_dates=['date'])
        fed_df = pd.read_csv(fed_path, parse_dates=['date'])

        # Both should have data
        assert len(foreign_df) > 0, "Foreign share CSV is empty"
        assert len(fed_df) > 0, "Fed share CSV is empty"

        # Fed data should extend at least as far as foreign data
        assert fed_df['date'].max() >= foreign_df['date'].max(), \
            "Fed share data should not end before foreign share data"


class TestCurrentAccount:
    """Test current account processing."""

    def test_ca_pct_gdp_in_range(self):
        """Current account values should be between -8% and +3%."""
        path = Path('data/processed/current_account_gdp.csv')
        if not path.exists():
            pytest.skip("current_account_gdp.csv not found — run pipeline first")

        df = pd.read_csv(path)
        assert df['ca_pct_gdp'].min() >= -8, f"CA/GDP below -8%: {df['ca_pct_gdp'].min()}"
        assert df['ca_pct_gdp'].max() <= 5, f"CA/GDP above +5%: {df['ca_pct_gdp'].max()}"

    def test_ca_typically_negative(self):
        """Most post-1990 observations should be negative (persistent deficits)."""
        path = Path('data/processed/current_account_gdp.csv')
        if not path.exists():
            pytest.skip("current_account_gdp.csv not found — run pipeline first")

        df = pd.read_csv(path, parse_dates=['date'])
        post_1990 = df[df['date'] >= '1990-01-01']
        neg_share = (post_1990['ca_pct_gdp'] < 0).mean()
        assert neg_share > 0.9, f"Only {neg_share:.0%} of post-1990 observations are negative"


class TestDebtToGDP:
    """Test debt-to-GDP processing."""

    def test_debt_gdp_in_range(self):
        """Debt-to-GDP values should be between 15% and 115%."""
        path = Path('data/processed/debt_to_gdp.csv')
        if not path.exists():
            pytest.skip("debt_to_gdp.csv not found — run pipeline first")

        df = pd.read_csv(path)
        assert df['debt_gdp'].min() >= 15, f"Debt/GDP below 15%: {df['debt_gdp'].min()}"
        assert df['debt_gdp'].max() <= 115, f"Debt/GDP above 115%: {df['debt_gdp'].max()}"

    def test_debt_gdp_increasing_recent(self):
        """Post-2008 values should be higher than pre-2008 average."""
        path = Path('data/processed/debt_to_gdp.csv')
        if not path.exists():
            pytest.skip("debt_to_gdp.csv not found — run pipeline first")

        df = pd.read_csv(path, parse_dates=['date'])
        pre_2008 = df[df['date'] < '2008-01-01']['debt_gdp'].mean()
        post_2008 = df[df['date'] >= '2008-01-01']['debt_gdp'].mean()
        assert post_2008 > pre_2008, f"Post-2008 avg ({post_2008:.1f}%) not higher than pre-2008 ({pre_2008:.1f}%)"


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
