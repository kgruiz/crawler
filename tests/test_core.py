"""Unit tests for the core StealthCrawler class."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from stealthcrawler.core import StealthCrawler


class TestStealthCrawlerInit:
    """Test StealthCrawler initialization."""

    def test_init_defaults(self):
        """Test initialization with default parameters."""
        crawler = StealthCrawler()

        assert crawler.base == []
        assert crawler.exclude == []
        assert not crawler.save_html
        assert not crawler.save_md
        assert not crawler.urls_only
        assert crawler.output_dir == Path("output")
        assert crawler.headless
        assert isinstance(crawler._seen, set)
        assert len(crawler._seen) == 0

    def test_init_single_base_string(self):
        """Test initialization with single base URL as string."""
        crawler = StealthCrawler(base="https://example.com")
        assert crawler.base == ["https://example.com"]

    def test_init_multiple_base_list(self):
        """Test initialization with multiple base URLs as list."""
        bases = ["https://example.com", "https://test.com"]
        crawler = StealthCrawler(base=bases)
        assert crawler.base == bases

    def test_init_single_exclude_string(self):
        """Test initialization with single exclude pattern as string."""
        crawler = StealthCrawler(exclude="https://example.com/admin")
        assert crawler.exclude == ["https://example.com/admin"]

    def test_init_multiple_exclude_list(self):
        """Test initialization with multiple exclude patterns as list."""
        excludes = ["https://example.com/admin", "https://example.com/private"]
        crawler = StealthCrawler(exclude=excludes)
        assert crawler.exclude == excludes

    def test_init_all_save_flags(self):
        """Test initialization with all save flags enabled."""
        crawler = StealthCrawler(
            save_html=True,
            save_md=True,
            urls_only=False,
            output_dir="/custom/output",
            headless=False,
        )

        assert crawler.save_html
        assert crawler.save_md
        assert not crawler.urls_only
        assert crawler.output_dir == Path("/custom/output")
        assert not crawler.headless


class TestFilterLinks:
    """Test the _filter_links method."""

    def test_filter_links_no_base_no_exclude(self):
        """Test filtering with no base or exclude patterns."""
        crawler = StealthCrawler()
        links = [
            "https://example.com/page1",
            "https://other.com/page2",
            "https://example.com/page3",
        ]

        result = crawler._filter_links(links)
        # Without base patterns, all links should be included
        assert len(result) == 3

    def test_filter_links_with_base(self):
        """Test filtering with base URL pattern."""
        crawler = StealthCrawler(base="https://example.com")
        links = [
            "https://example.com/page1",
            "https://other.com/page2",
            "https://example.com/page3",
            "https://different.com/page4",
        ]

        result = crawler._filter_links(links)
        expected = ["https://example.com/page1", "https://example.com/page3"]
        assert result == expected

    def test_filter_links_with_multiple_bases(self):
        """Test filtering with multiple base URL patterns."""
        crawler = StealthCrawler(base=["https://example.com", "https://test.com"])
        links = [
            "https://example.com/page1",
            "https://other.com/page2",
            "https://test.com/page3",
            "https://different.com/page4",
        ]

        result = crawler._filter_links(links)
        expected = ["https://example.com/page1", "https://test.com/page3"]
        assert result == expected

    def test_filter_links_with_exclude(self):
        """Test filtering with exclude patterns."""
        crawler = StealthCrawler(exclude="https://example.com/admin")
        links = [
            "https://example.com/page1",
            "https://example.com/admin/users",
            "https://example.com/admin/settings",
            "https://example.com/public",
        ]

        result = crawler._filter_links(links)
        expected = ["https://example.com/page1", "https://example.com/public"]
        assert result == expected

    def test_filter_links_with_multiple_excludes(self):
        """Test filtering with multiple exclude patterns."""
        crawler = StealthCrawler(
            exclude=["https://example.com/admin", "https://example.com/private"]
        )
        links = [
            "https://example.com/page1",
            "https://example.com/admin/users",
            "https://example.com/private/data",
            "https://example.com/public",
        ]

        result = crawler._filter_links(links)
        expected = ["https://example.com/page1", "https://example.com/public"]
        assert result == expected

    def test_filter_links_base_and_exclude(self):
        """Test filtering with both base and exclude patterns."""
        crawler = StealthCrawler(
            base="https://example.com", exclude="https://example.com/admin"
        )
        links = [
            "https://example.com/page1",
            "https://example.com/admin/users",
            "https://other.com/page2",
            "https://example.com/public",
        ]

        result = crawler._filter_links(links)
        expected = ["https://example.com/page1", "https://example.com/public"]
        assert result == expected

    @patch("stealthcrawler.core.normalize_url")
    def test_filter_links_normalizes_urls(self, mock_normalize):
        """Test that URLs are normalized during filtering."""
        mock_normalize.side_effect = lambda x: x.lower()

        crawler = StealthCrawler(base="https://example.com")
        links = ["HTTPS://EXAMPLE.COM/PAGE1"]

        crawler._filter_links(links)

        mock_normalize.assert_called_with("HTTPS://EXAMPLE.COM/PAGE1")


class TestTruncateUrl:
    """Test the _truncate_url method."""

    def test_truncate_short_url(self):
        """Test truncation of short URLs."""
        crawler = StealthCrawler()
        url = "https://example.com"
        result = crawler._truncate_url(url)
        assert result == url

    def test_truncate_long_url(self):
        """Test truncation of long URLs."""
        crawler = StealthCrawler()
        url = "https://example.com/very/long/path/to/some/resource/that/exceeds/forty/characters"
        result = crawler._truncate_url(url)

        assert len(result) <= len(url)
        assert result.startswith("https://example.com/")
        assert result.endswith("characters")
        assert "..." in result

    def test_truncate_exactly_40_chars(self):
        """Test URL that is exactly 40 characters."""
        crawler = StealthCrawler()
        url = "https://example.com/path/to/resource123"  # Exactly 40 chars
        result = crawler._truncate_url(url)
        assert result == url

    def test_truncate_41_chars(self):
        """Test URL that is 41 characters (should be truncated)."""
        crawler = StealthCrawler()
        url = "https://example.com/path/to/resource1234x"  # 41 chars
        result = crawler._truncate_url(url)

        assert len(result) < len(url)
        assert "..." in result


class TestProcessPageErrorHandling:
    """Test error handling scenarios for _process_page."""

    @pytest.mark.asyncio
    async def test_process_page_navigation_error(self):
        """Test handling of navigation errors."""
        crawler = StealthCrawler()

        # Mock page that fails to navigate
        page = AsyncMock()
        page.go_to.side_effect = Exception("Navigation failed")

        progress = MagicMock()
        task_id = "test_task"

        # Should not raise exception but handle gracefully
        with pytest.raises(Exception, match="Navigation failed"):
            await crawler._process_page(page, "https://invalid.url", progress, task_id)

    @pytest.mark.asyncio
    async def test_process_page_save_error(self):
        """Test handling of save errors."""
        crawler = StealthCrawler(save_html=True)

        page = AsyncMock()
        page.go_to.return_value = None
        page._wait_page_load.return_value = None

        progress = MagicMock()
        task_id = "test_task"

        with patch("stealthcrawler.core.save_html") as mock_save:
            mock_save.side_effect = Exception("Save failed")
            with patch("stealthcrawler.core.get_self_hrefs") as mock_get_hrefs:
                mock_get_hrefs.return_value = []

                # Should not raise exception but handle gracefully
                with pytest.raises(Exception, match="Save failed"):
                    await crawler._process_page(
                        page, "https://example.com", progress, task_id
                    )


class TestCrawlMethodEdgeCases:
    """Test edge cases for the crawl method."""

    @pytest.mark.asyncio
    async def test_crawl_sets_base_from_start_url(self):
        """Test that base URL is set from start URL when not provided."""
        crawler = StealthCrawler()
        assert crawler.base == []

        start_url = "https://example.com"

        with patch("stealthcrawler.core.Chrome") as mock_chrome:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_browser.start.return_value = mock_page
            mock_chrome.return_value.__aenter__.return_value = mock_browser

            with patch.object(crawler, "_process_page") as mock_process:
                mock_process.return_value = None
                with patch("stealthcrawler.core.make_progress") as mock_progress:
                    progress_instance = MagicMock()
                    progress_instance.__enter__.return_value = progress_instance
                    progress_instance.__exit__.return_value = None
                    mock_progress.return_value = progress_instance

                    await crawler.crawl(start_url)

        assert crawler.base == [start_url]

    @pytest.mark.asyncio
    async def test_crawl_skips_binary_files(self):
        """Test that binary file types are skipped."""
        crawler = StealthCrawler()
        crawler._stack.extend(
            [
                "https://example.com/file.zip",
                "https://example.com/doc.pdf",
                "https://example.com/video.m3u8",
                "https://example.com/page.html",
            ]
        )

        with patch("stealthcrawler.core.Chrome") as mock_chrome:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_browser.start.return_value = mock_page
            mock_chrome.return_value.__aenter__.return_value = mock_browser

            with patch.object(crawler, "_process_page") as mock_process:
                mock_process.return_value = None
                with patch("stealthcrawler.core.make_progress") as mock_progress:
                    progress_instance = MagicMock()
                    progress_instance.__enter__.return_value = progress_instance
                    progress_instance.__exit__.return_value = None
                    mock_progress.return_value = progress_instance

                    result = await crawler.crawl("https://example.com")

        # Binary files should be marked as seen but not processed
        assert "https://example.com/file.zip" in crawler._seen
        assert "https://example.com/doc.pdf" in crawler._seen
        assert "https://example.com/video.m3u8" in crawler._seen

        # _process_page should only be called twice: once for start URL, once for .html
        assert mock_process.call_count == 2

    @pytest.mark.asyncio
    async def test_crawl_creates_output_directories(self):
        """Test that output directories are created correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "test_output"

            crawler = StealthCrawler(
                save_html=True, save_md=True, output_dir=str(output_dir)
            )

            with patch("stealthcrawler.core.Chrome") as mock_chrome:
                mock_browser = AsyncMock()
                mock_page = AsyncMock()
                mock_browser.start.return_value = mock_page
                mock_chrome.return_value.__aenter__.return_value = mock_browser

                with patch.object(crawler, "_process_page") as mock_process:
                    mock_process.return_value = None
                    with patch("stealthcrawler.core.make_progress") as mock_progress:
                        progress_instance = MagicMock()
                        progress_instance.__enter__.return_value = progress_instance
                        progress_instance.__exit__.return_value = None
                        mock_progress.return_value = progress_instance

                        await crawler.crawl("https://example.com")

            # Check that directories were created
            assert output_dir.exists()
            assert (output_dir / "html").exists()
            assert (output_dir / "markdown").exists()
