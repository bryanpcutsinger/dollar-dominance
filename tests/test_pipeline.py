"""Smoke tests for the pipeline."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestNoFetchMode:
    """Test that --no-fetch mode works with cached data."""

    def test_processed_csvs_exist(self):
        """After processing, expected output files should exist."""
        proc_dir = Path('data/processed')
        # These should exist after any successful run
        expected = ['cofer_shares.csv', 'fx_turnover_triennial.csv', 'metadata.json']
        for f in expected:
            path = proc_dir / f
            assert path.exists(), f"Expected {path} to exist"

    def test_metadata_valid_json(self):
        """metadata.json should be valid JSON with expected keys."""
        meta_path = Path('data/processed/metadata.json')
        if not meta_path.exists():
            pytest.skip("metadata.json not found — run pipeline first")

        with open(meta_path) as f:
            meta = json.load(f)

        assert 'last_updated' in meta
        assert 'sources' in meta
        assert isinstance(meta['sources'], dict)

    def test_dashboard_html_exists(self):
        """output/index.html should exist after build."""
        path = Path('output/index.html')
        assert path.exists(), "Dashboard HTML not found — run pipeline first"

    def test_dashboard_contains_plotly(self):
        """Dashboard HTML should reference Plotly CDN."""
        path = Path('output/index.html')
        if not path.exists():
            pytest.skip("Dashboard not built yet")

        with open(path) as f:
            html = f.read()

        assert 'plotly' in html.lower()
        assert 'Dollar Dominance Dashboard' in html

    def test_dashboard_under_10mb(self):
        """Dashboard HTML should be under 10MB."""
        path = Path('output/index.html')
        if not path.exists():
            pytest.skip("Dashboard not built yet")

        size_mb = path.stat().st_size / (1024 * 1024)
        assert size_mb < 10, f"Dashboard is {size_mb:.1f}MB — exceeds 10MB limit"
