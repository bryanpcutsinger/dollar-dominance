"""Tests for new dashboard components: metric cards, key takeaways, qualitative sections."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestMetricCards:
    """Test metric card generation."""

    def test_metric_cards_returns_html(self):
        """build_metric_cards should return a non-empty HTML string."""
        from src.build_components import build_metric_cards
        result = build_metric_cards()
        assert isinstance(result, str)
        # Should contain grid wrapper if data exists
        if result:
            assert 'metric-cards-grid' in result

    def test_metric_cards_contain_values(self):
        """Cards should contain percentage values or index values."""
        from src.build_components import build_metric_cards
        result = build_metric_cards()
        if not result:
            pytest.skip("No processed data available")
        assert 'card-value' in result
        assert '%' in result or 'DXY' in result


class TestKeyTakeaways:
    """Test key takeaways generation."""

    def test_key_takeaways_returns_html(self):
        """build_key_takeaways should return HTML with list items."""
        from src.build_components import build_key_takeaways
        result = build_key_takeaways()
        if not result:
            pytest.skip("No processed data available")
        assert '<li>' in result
        assert 'key-takeaways' in result


class TestStickyHeader:
    """Test sticky header generation."""

    def test_sticky_header_returns_html(self):
        """build_sticky_header should return HTML with values."""
        from src.build_components import build_sticky_header
        result = build_sticky_header()
        if not result:
            pytest.skip("No processed data available")
        assert 'sticky-header' in result
        assert 'sticky-value' in result


class TestTreasuriesTakeaways:
    """Test treasuries takeaway generation."""

    def test_treasuries_takeaways_returns_html(self):
        """build_treasuries_takeaways should return HTML with FRED reference."""
        from src.build_components import build_treasuries_takeaways
        result = build_treasuries_takeaways()
        if not result:
            pytest.skip("No treasury data available")
        assert 'FRED' in result
        assert 'key-takeaways' in result


class TestQualitativeData:
    """Test qualitative/editorial content rendering."""

    def test_methodology_html(self):
        """Methodology should contain key section headers."""
        from src.qualitative_data import methodology_html
        result = methodology_html()
        assert 'COFER' in result
        assert 'BIS' in result
        assert 'DTWEXBGS' in result
        assert 'FDHBFIN' in result


class TestDeltaFormatting:
    """Test delta/change formatting logic."""

    def test_positive_delta(self):
        """Positive delta should show green arrow."""
        from src.build_components import _delta_html
        result = _delta_html(1.5)
        assert '0d7a3f' in result  # green color (colorblind-safe)
        assert '+1.5' in result

    def test_negative_delta(self):
        """Negative delta should show red arrow."""
        from src.build_components import _delta_html
        result = _delta_html(-2.3)
        assert 'c22a2a' in result  # red color
        assert '-2.3' in result

    def test_zero_delta(self):
        """Near-zero delta should show gray dash."""
        from src.build_components import _delta_html
        result = _delta_html(0.01)
        assert '737385' in result  # gray
