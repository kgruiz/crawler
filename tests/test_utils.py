"""Tests for utility functions."""

import shutil
import tempfile
from pathlib import Path

import pytest

from stealthcrawler.utils import ensure_dir, normalize_url, safe_filename


class TestNormalizeUrl:
    """Test normalize_url function."""

    def test_removes_fragment(self):
        """Test that URL fragments are removed."""
        url = "https://example.com/page#section"
        result = normalize_url(url)
        assert result == "https://example.com/page"

    def test_no_fragment(self):
        """Test URL without fragment is unchanged."""
        url = "https://example.com/page"
        result = normalize_url(url)
        assert result == url

    def test_empty_fragment(self):
        """Test URL with empty fragment."""
        url = "https://example.com/page#"
        result = normalize_url(url)
        assert result == "https://example.com/page"


class TestSafeFilename:
    """Test safe_filename function."""

    def test_basic_url(self):
        """Test basic URL conversion."""
        url = "https://example.com/path/to/page"
        result = safe_filename(url)
        assert result == "example.com_path_to_page"

    def test_with_extension(self):
        """Test URL conversion with extension."""
        url = "https://example.com/path/to/page"
        result = safe_filename(url, ".html")
        assert result == "example.com_path_to_page.html"

    def test_root_path(self):
        """Test URL with root path defaults to index."""
        url = "https://example.com/"
        result = safe_filename(url)
        assert result == "example.com_index"

    def test_no_path(self):
        """Test URL with no path defaults to index."""
        url = "https://example.com"
        result = safe_filename(url)
        assert result == "example.com_index"


class TestEnsureDir:
    """Test ensure_dir function."""

    def test_creates_directory(self):
        """Test that directory is created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / "test_dir"
            assert not test_path.exists()

            ensure_dir(test_path)

            assert test_path.exists()
            assert test_path.is_dir()

    def test_creates_nested_directories(self):
        """Test that nested directories are created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / "nested" / "test_dir"
            assert not test_path.exists()

            ensure_dir(test_path)

            assert test_path.exists()
            assert test_path.is_dir()

    def test_existing_directory(self):
        """Test that existing directory is not affected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir)
            assert test_path.exists()

            # Should not raise exception
            ensure_dir(test_path)
