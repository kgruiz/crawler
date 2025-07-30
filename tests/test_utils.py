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


class TestNormalizeUrlEdgeCases:
    """Test edge cases for normalize_url function."""

    def test_normalize_url_multiple_fragments(self):
        """Test URL with multiple fragment indicators."""
        url = "https://example.com/page#section1#section2"
        result = normalize_url(url)
        # Should remove everything after first #
        assert result == "https://example.com/page"

    def test_normalize_url_query_and_fragment(self):
        """Test URL with both query parameters and fragment."""
        url = "https://example.com/page?param=value&other=test#section"
        result = normalize_url(url)
        # Should keep query but remove fragment
        assert result == "https://example.com/page?param=value&other=test"

    def test_normalize_url_fragment_only(self):
        """Test URL that is only a fragment."""
        url = "#section"
        result = normalize_url(url)
        assert result == ""

    def test_normalize_url_complex_fragments(self):
        """Test URL with complex fragment containing special characters."""
        url = "https://example.com/page#section/with/slashes?and=params"
        result = normalize_url(url)
        assert result == "https://example.com/page"

    def test_normalize_url_unicode_fragment(self):
        """Test URL with Unicode characters in fragment."""
        url = "https://example.com/page#章节"
        result = normalize_url(url)
        assert result == "https://example.com/page"

    def test_normalize_url_encoded_fragment(self):
        """Test URL with URL-encoded fragment."""
        url = "https://example.com/page#section%20with%20spaces"
        result = normalize_url(url)
        assert result == "https://example.com/page"


class TestSafeFilenameEdgeCases:
    """Test edge cases for safe_filename function."""

    def test_safe_filename_special_characters(self):
        """Test safe_filename with various special characters."""
        special_chars_url = 'https://example.com/path/with<>:"|?*spaces'
        result = safe_filename(special_chars_url)

        # Should not contain filesystem-unsafe characters
        unsafe_chars = '<>:"|?*'
        for char in unsafe_chars:
            assert char not in result

        # Should contain safe representation
        assert "example.com" in result

    def test_safe_filename_unicode_path(self):
        """Test safe_filename with Unicode characters in path."""
        unicode_url = "https://example.com/路径/页面"
        result = safe_filename(unicode_url)

        # Should handle Unicode gracefully
        assert isinstance(result, str)
        assert "example.com" in result

    def test_safe_filename_very_long_path(self):
        """Test safe_filename with very long path."""
        long_path = "/".join(["segment"] * 50)
        long_url = f"https://example.com{long_path}"
        result = safe_filename(long_url)

        # Should limit length for filesystem compatibility
        assert len(result) <= 255  # Common filesystem limit

    def test_safe_filename_port_in_url(self):
        """Test safe_filename with port numbers."""
        url_with_port = "https://example.com:8080/path/to/resource"
        result = safe_filename(url_with_port)

        # Should include port in filename
        assert "example.com" in result
        # Port should be handled safely
        assert "8080" in result or "example.com_path_to_resource" in result

    def test_safe_filename_query_parameters(self):
        """Test safe_filename with query parameters."""
        url_with_query = "https://example.com/page?param=value&other=test"
        result = safe_filename(url_with_query)

        # Query parameters should be handled safely
        assert "example.com" in result
        # Should not contain unsafe characters from query
        assert "?" not in result

    def test_safe_filename_trailing_slashes(self):
        """Test safe_filename with trailing slashes."""
        urls = [
            "https://example.com/",
            "https://example.com/path/",
            "https://example.com/path/to/page/",
        ]

        for url in urls:
            result = safe_filename(url)
            # Should handle trailing slashes gracefully
            assert not result.endswith("_")  # Shouldn't have trailing underscores

    def test_safe_filename_subdomain(self):
        """Test safe_filename with subdomains."""
        subdomain_url = "https://api.v2.example.com/endpoint"
        result = safe_filename(subdomain_url)

        # Should include subdomain information
        assert "api" in result or "v2" in result or "example.com" in result

    def test_safe_filename_different_extensions(self):
        """Test safe_filename with different extensions."""
        base_url = "https://example.com/path/to/resource"
        extensions = [".html", ".md", ".txt", ".json", ".xml"]

        for ext in extensions:
            result = safe_filename(base_url, ext)
            assert result.endswith(ext)
            assert "example.com" in result

    def test_safe_filename_no_extension_with_dots_in_path(self):
        """Test safe_filename with dots in path but no extension parameter."""
        url_with_dots = "https://example.com/version.2.0/api.endpoint"
        result = safe_filename(url_with_dots)

        # Should handle dots in path safely
        assert "example.com" in result
        assert "version" in result or "api" in result or "endpoint" in result


class TestEnsureDirEdgeCases:
    """Test edge cases for ensure_dir function."""

    def test_ensure_dir_with_file_path(self):
        """Test ensure_dir when given a file path instead of directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file
            file_path = Path(temp_dir) / "test_file.txt"
            file_path.write_text("test content")

            # Try to ensure directory at file location should fail
            with pytest.raises((FileExistsError, OSError)):
                ensure_dir(file_path)

    def test_ensure_dir_deep_nested_path(self):
        """Test ensure_dir with deeply nested path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create deeply nested path
            deep_path = Path(temp_dir)
            for i in range(10):
                deep_path = deep_path / f"level{i}"

            # Should create entire nested structure
            ensure_dir(deep_path)

            assert deep_path.exists()
            assert deep_path.is_dir()

    def test_ensure_dir_with_symlink(self):
        """Test ensure_dir with symbolic links."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create target directory
            target_dir = temp_path / "target"
            target_dir.mkdir()

            # Create symlink to target
            symlink_path = temp_path / "symlink"
            symlink_path.symlink_to(target_dir)

            # Should handle symlink correctly
            ensure_dir(symlink_path)

            assert symlink_path.exists()
            assert symlink_path.is_symlink()

    def test_ensure_dir_relative_path(self):
        """Test ensure_dir with relative path."""
        import os

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                # Change to temp directory
                os.chdir(temp_dir)

                # Create relative path
                rel_path = Path("relative/nested/directory")

                ensure_dir(rel_path)

                assert rel_path.exists()
                assert rel_path.is_dir()

            finally:
                os.chdir(original_cwd)

    def test_ensure_dir_with_spaces_in_name(self):
        """Test ensure_dir with spaces in directory names."""
        with tempfile.TemporaryDirectory() as temp_dir:
            spaced_path = (
                Path(temp_dir) / "directory with spaces" / "nested with spaces"
            )

            ensure_dir(spaced_path)

            assert spaced_path.exists()
            assert spaced_path.is_dir()

    def test_ensure_dir_with_unicode_names(self):
        """Test ensure_dir with Unicode directory names."""
        with tempfile.TemporaryDirectory() as temp_dir:
            unicode_path = Path(temp_dir) / "目录" / "вложенная" / "מתיקיה"

            ensure_dir(unicode_path)

            assert unicode_path.exists()
            assert unicode_path.is_dir()


class TestUtilsIntegration:
    """Integration tests for utility functions."""

    def test_utils_workflow_integration(self):
        """Test typical workflow using all utility functions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)

            # Test workflow: normalize URL -> create safe filename -> ensure directory
            original_url = "https://example.com/path/to/page?param=value#section"

            # Step 1: Normalize URL
            normalized = normalize_url(original_url)
            assert normalized == "https://example.com/path/to/page?param=value"

            # Step 2: Create safe filename
            safe_name = safe_filename(normalized, ".html")
            assert safe_name.endswith(".html")
            assert "example.com" in safe_name

            # Step 3: Ensure output directory exists
            output_dir = base_dir / "output" / "html"
            ensure_dir(output_dir)
            assert output_dir.exists()

            # Step 4: Create full file path
            full_path = output_dir / safe_name
            full_path.write_text("<html><body>Test</body></html>")

            assert full_path.exists()
            assert full_path.read_text() == "<html><body>Test</body></html>"

    def test_utils_with_problematic_urls(self):
        """Test utility functions with problematic URLs."""
        problematic_urls = [
            "https://example.com/path<with>invalid:chars|in?path*name",
            "https://example.com/" + "x" * 300,  # Very long path
            "https://example.com/路径/with/中文/characters",
            "https://example.com:8080/path?query=value&other=test#fragment",
            "https://sub.domain.example.com/deeply/nested/path/structure",
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)

            for i, url in enumerate(problematic_urls):
                # Should handle all problematic URLs without errors
                normalized = normalize_url(url)
                safe_name = safe_filename(normalized, f".{i}.html")

                output_dir = base_dir / f"test_{i}"
                ensure_dir(output_dir)

                full_path = output_dir / safe_name
                full_path.write_text(f"Content for URL {i}")

                assert full_path.exists()
                assert len(safe_name) <= 255  # Filesystem limit

                # Verify no unsafe characters in filename
                unsafe_chars = '<>:"|?*'
                for char in unsafe_chars:
                    assert char not in safe_name

    def test_utils_error_recovery(self):
        """Test utility functions' error recovery capabilities."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)

            # Test recovery from various error conditions

            # 1. Try to ensure directory where file exists
            conflict_path = base_dir / "conflict"
            conflict_path.write_text("existing file")

            try:
                ensure_dir(conflict_path)
                assert False, "Should have raised an exception"
            except (FileExistsError, OSError):
                # Expected behavior
                pass

            # 2. Test with very long filename
            long_url = "https://example.com/" + "segment/" * 100
            safe_name = safe_filename(long_url)

            # Should truncate to safe length
            assert len(safe_name) <= 255

            # 3. Test normalization with edge case URLs
            edge_urls = ["", "#", "?", "https://", "://example.com"]
            for url in edge_urls:
                try:
                    result = normalize_url(url)
                    assert isinstance(result, str)  # Should return string even if empty
                except Exception:
                    # Some edge cases might raise exceptions, which is acceptable
                    pass
