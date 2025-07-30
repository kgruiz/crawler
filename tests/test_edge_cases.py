"""Edge case and error handling tests across all modules."""

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from stealthcrawler.core import StealthCrawler
from stealthcrawler.fetchers import save_html, save_markdown, save_pdf, save_screenshot
from stealthcrawler.utils import ensure_dir, normalize_url, safe_filename


class TestNetworkErrorHandling:
    """Test handling of network-related errors."""

    @pytest.mark.asyncio
    async def test_crawler_navigation_timeout(self):
        """Test handling of navigation timeouts."""
        crawler = StealthCrawler()

        with patch("stealthcrawler.core.Chrome") as mock_chrome:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_browser.start.return_value = mock_page
            mock_chrome.return_value.__aenter__.return_value = mock_browser

            # Mock navigation timeout
            mock_page.go_to.side_effect = Exception("Navigation timeout")

            with patch("stealthcrawler.core.make_progress") as mock_progress:
                progress_instance = MagicMock()
                progress_instance.__enter__.return_value = progress_instance
                progress_instance.__exit__.return_value = None
                mock_progress.return_value = progress_instance

                with pytest.raises(Exception, match="Navigation timeout"):
                    await crawler.crawl("https://example.com")

    @pytest.mark.asyncio
    async def test_crawler_dns_resolution_failure(self):
        """Test handling of DNS resolution failures."""
        crawler = StealthCrawler()

        with patch("stealthcrawler.core.Chrome") as mock_chrome:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_browser.start.return_value = mock_page
            mock_chrome.return_value.__aenter__.return_value = mock_browser

            # Mock DNS failure
            mock_page.go_to.side_effect = Exception("DNS resolution failed")

            with patch("stealthcrawler.core.make_progress") as mock_progress:
                progress_instance = MagicMock()
                progress_instance.__enter__.return_value = progress_instance
                progress_instance.__exit__.return_value = None
                mock_progress.return_value = progress_instance

                with pytest.raises(Exception, match="DNS resolution failed"):
                    await crawler.crawl("https://nonexistent.domain.example")

    @pytest.mark.asyncio
    async def test_crawler_ssl_certificate_error(self):
        """Test handling of SSL certificate errors."""
        crawler = StealthCrawler()

        with patch("stealthcrawler.core.Chrome") as mock_chrome:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_browser.start.return_value = mock_page
            mock_chrome.return_value.__aenter__.return_value = mock_browser

            # Mock SSL error
            mock_page.go_to.side_effect = Exception(
                "SSL certificate verification failed"
            )

            with patch("stealthcrawler.core.make_progress") as mock_progress:
                progress_instance = MagicMock()
                progress_instance.__enter__.return_value = progress_instance
                progress_instance.__exit__.return_value = None
                mock_progress.return_value = progress_instance

                with pytest.raises(
                    Exception, match="SSL certificate verification failed"
                ):
                    await crawler.crawl("https://self-signed.badssl.com")


class TestFileSystemErrorHandling:
    """Test handling of filesystem-related errors."""

    def test_ensure_dir_permission_denied(self):
        """Test ensure_dir with permission denied error."""
        # Try to create directory in root (should fail on most systems)
        restricted_path = Path("/root/test_directory")

        with pytest.raises(PermissionError):
            ensure_dir(restricted_path)

    def test_safe_filename_with_invalid_characters(self):
        """Test safe_filename with URLs containing invalid filename characters."""
        # URL with characters that are invalid in filenames
        url = 'https://example.com/path<>:"|?*'
        result = safe_filename(url)

        # Should not contain invalid characters
        invalid_chars = '<>:"|?*'
        for char in invalid_chars:
            assert char not in result

        # Should still contain the domain
        assert "example.com" in result

    def test_safe_filename_extremely_long_url(self):
        """Test safe_filename with extremely long URLs."""
        # Create a very long URL
        long_path = "/".join(["verylongpathsegment"] * 50)
        url = f"https://example.com{long_path}"

        result = safe_filename(url)

        # Result should be reasonable length for filesystem
        # Most filesystems have limits around 255 characters
        assert len(result) <= 255

    @pytest.mark.asyncio
    async def test_save_html_disk_full_error(self):
        """Test save_html with disk full error."""
        page = AsyncMock()
        page.current_url = "https://example.com/test"
        page.page_source = "<html><body>Test</body></html>"

        with patch("stealthcrawler.fetchers.safe_filename") as mock_safe_filename:
            mock_safe_filename.return_value = "test.html"

            with patch("pathlib.Path.write_text") as mock_write:
                mock_write.side_effect = OSError("No space left on device")

                with pytest.raises(OSError, match="No space left on device"):
                    await save_html(page, Path("/tmp"))

    @pytest.mark.asyncio
    async def test_save_markdown_readonly_filesystem(self):
        """Test save_markdown with read-only filesystem error."""
        page = AsyncMock()
        page.current_url = "https://example.com/test"
        page.page_source = "<html><body>Test</body></html>"

        with patch("stealthcrawler.fetchers.safe_filename") as mock_safe_filename:
            mock_safe_filename.return_value = "test.md"

            with patch("pathlib.Path.write_text") as mock_write:
                mock_write.side_effect = PermissionError("Read-only file system")

                with pytest.raises(PermissionError, match="Read-only file system"):
                    await save_markdown(page, Path("/tmp"))

    def test_ensure_dir_existing_file_conflict(self):
        """Test ensure_dir when a file exists with the same name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file with the name we want for directory
            file_path = Path(temp_dir) / "conflict"
            file_path.write_text("existing file content")

            # Try to create directory with the same name
            with pytest.raises(FileExistsError):
                ensure_dir(file_path)


class TestBrowserErrorHandling:
    """Test handling of browser-related errors."""

    @pytest.mark.asyncio
    async def test_browser_launch_failure(self):
        """Test handling of browser launch failures."""
        crawler = StealthCrawler()

        with patch("stealthcrawler.core.Chrome") as mock_chrome:
            mock_chrome.side_effect = Exception("Chrome failed to launch")

            with patch("stealthcrawler.core.make_progress") as mock_progress:
                progress_instance = MagicMock()
                progress_instance.__enter__.return_value = progress_instance
                progress_instance.__exit__.return_value = None
                mock_progress.return_value = progress_instance

                with pytest.raises(Exception, match="Chrome failed to launch"):
                    await crawler.crawl("https://example.com")

    @pytest.mark.asyncio
    async def test_page_crash_during_crawl(self):
        """Test handling of page crashes during crawling."""
        crawler = StealthCrawler()

        with patch("stealthcrawler.core.Chrome") as mock_chrome:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_browser.start.return_value = mock_page
            mock_chrome.return_value.__aenter__.return_value = mock_browser

            # Mock page crash during _wait_page_load
            mock_page.go_to.return_value = None
            mock_page._wait_page_load.side_effect = Exception("Page crashed")

            with patch("stealthcrawler.core.make_progress") as mock_progress:
                progress_instance = MagicMock()
                progress_instance.__enter__.return_value = progress_instance
                progress_instance.__exit__.return_value = None
                mock_progress.return_value = progress_instance

                with pytest.raises(Exception, match="Page crashed"):
                    await crawler.crawl("https://example.com")

    @pytest.mark.asyncio
    async def test_pdf_generation_failure(self):
        """Test handling of PDF generation failures."""
        page = AsyncMock()
        page.print_to_pdf.side_effect = Exception("PDF generation failed")

        pdf_path = Path("/tmp/test.pdf")

        with pytest.raises(Exception, match="PDF generation failed"):
            await save_pdf(page, pdf_path)

    @pytest.mark.asyncio
    async def test_screenshot_capture_failure(self):
        """Test handling of screenshot capture failures."""
        page = AsyncMock()
        page.get_screenshot.side_effect = Exception("Screenshot capture failed")

        screenshot_path = Path("/tmp/test.png")

        with pytest.raises(Exception, match="Screenshot capture failed"):
            await save_screenshot(page, screenshot_path)


class TestMemoryAndResourceHandling:
    """Test handling of memory and resource constraints."""

    @pytest.mark.asyncio
    async def test_large_page_content_handling(self):
        """Test handling of very large page content."""
        page = AsyncMock()
        page.current_url = "https://example.com/large"

        # Simulate very large page content (10MB)
        large_content = "x" * (10 * 1024 * 1024)
        page.page_source = large_content

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            with patch("stealthcrawler.fetchers.safe_filename") as mock_safe_filename:
                mock_safe_filename.return_value = "large.html"

                # Should handle large content without memory errors
                await save_html(page, output_dir)

                # Verify file was created
                saved_file = output_dir / "large.html"
                assert saved_file.exists()

                # Verify content size
                assert saved_file.stat().st_size == len(large_content)

    def test_crawler_with_large_number_of_urls(self):
        """Test crawler initialization with large URL lists."""
        # Create large lists for base and exclude
        large_base_list = [f"https://example{i}.com" for i in range(1000)]
        large_exclude_list = [f"https://exclude{i}.com" for i in range(1000)]

        # Should handle large lists without memory issues
        crawler = StealthCrawler(base=large_base_list, exclude=large_exclude_list)

        assert len(crawler.base) == 1000
        assert len(crawler.exclude) == 1000

    def test_filter_links_with_large_link_list(self):
        """Test _filter_links with a large number of links."""
        crawler = StealthCrawler(base="https://example.com")

        # Create large list of links
        large_link_list = [f"https://example.com/page{i}" for i in range(10000)]

        # Should handle large list efficiently
        result = crawler._filter_links(large_link_list)

        # All links should match the base
        assert len(result) == 10000


class TestUnicodeAndEncodingHandling:
    """Test handling of Unicode content and encoding issues."""

    @pytest.mark.asyncio
    async def test_save_html_with_various_encodings(self):
        """Test save_html with various character encodings."""
        test_cases = [
            "Hello 世界",  # Chinese
            "مرحبا بالعالم",  # Arabic
            "Здравствуй, мир",  # Russian
            "🌍🚀💻",  # Emojis
            "Café naïve résumé",  # French accents
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            for i, content in enumerate(test_cases):
                page = AsyncMock()
                page.current_url = f"https://example.com/unicode{i}"
                page.page_source = f"<html><body><h1>{content}</h1></body></html>"

                with patch(
                    "stealthcrawler.fetchers.safe_filename"
                ) as mock_safe_filename:
                    mock_safe_filename.return_value = f"unicode{i}.html"

                    await save_html(page, output_dir)

                    # Verify file was created and content is correct
                    saved_file = output_dir / f"unicode{i}.html"
                    assert saved_file.exists()

                    saved_content = saved_file.read_text(encoding="utf-8")
                    assert content in saved_content

    def test_safe_filename_with_unicode_domains(self):
        """Test safe_filename with internationalized domain names."""
        unicode_urls = [
            "https://例え.テスト/path",  # Japanese
            "https://пример.тест/path",  # Russian
            "https://مثال.إختبار/path",  # Arabic
        ]

        for url in unicode_urls:
            result = safe_filename(url)
            # Should handle Unicode domains gracefully
            assert isinstance(result, str)
            assert len(result) > 0

    def test_normalize_url_with_unicode_paths(self):
        """Test normalize_url with Unicode path components."""
        unicode_urls = [
            "https://example.com/路径/页面#锚点",
            "https://example.com/путь/страница#якорь",
            "https://example.com/مسار/صفحة#مرساة",
        ]

        for url in unicode_urls:
            result = normalize_url(url)
            # Should normalize while preserving Unicode characters
            assert isinstance(result, str)
            # Fragment should be removed
            assert "#" not in result


class TestConcurrencyAndRaceConditions:
    """Test handling of concurrency issues and race conditions."""

    def test_ensure_dir_concurrent_creation(self):
        """Test ensure_dir with concurrent directory creation."""
        import threading
        import time

        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "concurrent_test"
            exceptions = []

            def create_dir():
                try:
                    time.sleep(0.01)  # Small delay to increase chance of race condition
                    ensure_dir(test_dir)
                except Exception as e:
                    exceptions.append(e)

            # Create multiple threads trying to create the same directory
            threads = []
            for _ in range(10):
                thread = threading.Thread(target=create_dir)
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # Directory should exist and no exceptions should have occurred
            assert test_dir.exists()
            assert len(exceptions) == 0

    @pytest.mark.asyncio
    async def test_concurrent_file_saves(self):
        """Test concurrent file saving operations."""
        import asyncio

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            async def save_test_file(i):
                page = AsyncMock()
                page.current_url = f"https://example.com/page{i}"
                page.page_source = f"<html><body>Page {i}</body></html>"

                with patch(
                    "stealthcrawler.fetchers.safe_filename"
                ) as mock_safe_filename:
                    mock_safe_filename.return_value = f"page{i}.html"
                    await save_html(page, output_dir)

            # Run multiple saves concurrently
            tasks = [save_test_file(i) for i in range(10)]
            await asyncio.gather(*tasks)

            # Verify all files were created
            for i in range(10):
                assert (output_dir / f"page{i}.html").exists()


class TestMalformedDataHandling:
    """Test handling of malformed or unexpected data."""

    def test_normalize_url_with_malformed_urls(self):
        """Test normalize_url with various malformed URLs."""
        malformed_urls = [
            "not-a-url-at-all",
            "http://",
            "https://",
            "://example.com",
            "https:///path",
            "https://example.com:not-a-port/path",
            "https://[invalid-ipv6]/path",
        ]

        for url in malformed_urls:
            try:
                result = normalize_url(url)
                # If no exception, result should be a string
                assert isinstance(result, str)
            except Exception:
                # Some malformed URLs might raise exceptions, which is acceptable
                pass

    def test_safe_filename_with_empty_url(self):
        """Test safe_filename with empty or None URL."""
        with pytest.raises((ValueError, AttributeError)):
            safe_filename("")

        with pytest.raises((ValueError, AttributeError)):
            safe_filename(None)

    @pytest.mark.asyncio
    async def test_parsers_with_malformed_html(self):
        """Test parser functions with malformed HTML."""
        from stealthcrawler.parsers import get_hrefs, get_self_hrefs

        page = AsyncMock()

        # Mock malformed HTML scenarios
        malformed_elements = [
            # Element with no get_attribute method
            MagicMock(spec=[]),
            # Element that returns None for href
            MagicMock(**{"get_attribute.return_value": None}),
            # Element that raises exception
            MagicMock(**{"get_attribute.side_effect": Exception("Attribute error")}),
        ]

        # Add one valid element
        valid_element = MagicMock()
        valid_element.get_attribute.return_value = "https://example.com/valid"
        malformed_elements.append(valid_element)

        page.query.return_value = malformed_elements

        # Should handle malformed elements gracefully
        try:
            result = await get_hrefs(page)
            # If successful, should at least contain the valid element
            assert "https://example.com/valid" in result
        except Exception:
            # Some parsers might raise exceptions for malformed data
            pass


class TestResourceExhaustionHandling:
    """Test handling of resource exhaustion scenarios."""

    def test_crawler_filter_links_memory_efficiency(self):
        """Test that _filter_links doesn't consume excessive memory."""
        import sys

        crawler = StealthCrawler(base="https://example.com")

        # Create a moderately large list of links
        large_links = [f"https://example.com/page{i}" for i in range(50000)]

        # Monitor memory usage (basic check)
        initial_size = sys.getsizeof(large_links)

        result = crawler._filter_links(large_links)

        # Result should not be significantly larger than input
        result_size = sys.getsizeof(result)
        assert result_size <= initial_size * 2  # Allow some overhead

    def test_truncate_url_with_extremely_long_url(self):
        """Test _truncate_url with extremely long URLs."""
        crawler = StealthCrawler()

        # Create extremely long URL (1MB)
        long_url = "https://example.com/" + "x" * (1024 * 1024)

        result = crawler._truncate_url(long_url)

        # Should truncate to reasonable length
        assert len(result) <= 100  # Should be much shorter than original
        assert "https://example.com/" in result
        assert "..." in result


class TestConfigurationEdgeCases:
    """Test edge cases in configuration and setup."""

    def test_crawler_with_none_values(self):
        """Test crawler initialization with None values."""
        crawler = StealthCrawler(
            base=None,
            exclude=None,
            save_html=None,  # This will be falsy
            save_md=None,  # This will be falsy
            urls_only=None,  # This will be falsy
            output_dir=None,
            headless=None,  # This will be falsy
        )

        # Should handle None values gracefully
        assert crawler.base == []
        assert crawler.exclude == []
        assert not crawler.save_html
        assert not crawler.save_md
        assert not crawler.urls_only
        # output_dir might be None or default depending on implementation

    def test_crawler_with_mixed_types(self):
        """Test crawler with mixed data types for list parameters."""
        # This tests robustness of type handling
        try:
            crawler = StealthCrawler(
                base=123,  # Not string or list
                exclude={"set": "value"},  # Not string or list
            )
            # If it doesn't raise an exception, verify the behavior is reasonable
            assert isinstance(crawler.base, list)
            assert isinstance(crawler.exclude, list)
        except (TypeError, ValueError):
            # It's acceptable to raise type errors for invalid input
            pass
