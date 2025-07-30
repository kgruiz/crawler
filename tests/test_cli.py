"""Tests for CLI functionality."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from stealthcrawler.cli import crawl, main


class TestCliCrawlCommand:
    """Test the crawl CLI command."""

    def test_crawl_basic_url_only(self):
        """Test basic crawl command with urls-only flag."""
        runner = CliRunner()

        with patch("stealthcrawler.cli.StealthCrawler") as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler_class.return_value = mock_crawler

            with patch("stealthcrawler.cli.asyncio.run") as mock_asyncio_run:
                mock_asyncio_run.return_value = {
                    "https://example.com",
                    "https://example.com/page1",
                    "https://example.com/page2",
                }

                result = runner.invoke(crawl, ["https://example.com", "--urls-only"])

                assert result.exit_code == 0

                # Verify crawler was created with correct parameters
                mock_crawler_class.assert_called_once_with(
                    base=None,
                    exclude=None,
                    save_html=False,
                    save_md=False,
                    urls_only=True,
                    output_dir="output",
                    headless=True,
                )

                # Verify output contains URLs
                assert "https://example.com" in result.output
                assert "https://example.com/page1" in result.output
                assert "https://example.com/page2" in result.output

    def test_crawl_with_content_saving(self):
        """Test crawl command with content saving options."""
        runner = CliRunner()

        with patch("stealthcrawler.cli.StealthCrawler") as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler_class.return_value = mock_crawler

            with patch("stealthcrawler.cli.asyncio.run") as mock_asyncio_run:
                mock_asyncio_run.return_value = {"https://example.com"}

                result = runner.invoke(
                    crawl,
                    [
                        "https://example.com",
                        "--save-html",
                        "--save-md",
                        "--output-dir",
                        "/custom/output",
                    ],
                )

                assert result.exit_code == 0

                # Verify crawler was created with correct parameters
                mock_crawler_class.assert_called_once_with(
                    base=None,
                    exclude=None,
                    save_html=True,
                    save_md=True,
                    urls_only=False,
                    output_dir="/custom/output",
                    headless=True,
                )

                # Verify success message and output directory info
                assert "Successfully crawled 1 pages" in result.output
                assert "Content saved to:" in result.output

    def test_crawl_with_base_url(self):
        """Test crawl command with base URL parameter."""
        runner = CliRunner()

        with patch("stealthcrawler.cli.StealthCrawler") as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler_class.return_value = mock_crawler

            with patch("stealthcrawler.cli.asyncio.run") as mock_asyncio_run:
                mock_asyncio_run.return_value = {"https://example.com"}

                result = runner.invoke(
                    crawl,
                    ["https://example.com/start", "--base", "https://example.com"],
                )

                assert result.exit_code == 0

                # Verify base parameter was passed correctly
                mock_crawler_class.assert_called_once_with(
                    base="https://example.com",
                    exclude=None,
                    save_html=False,
                    save_md=False,
                    urls_only=False,
                    output_dir="output",
                    headless=True,
                )

    def test_crawl_with_exclude_single(self):
        """Test crawl command with single exclude pattern."""
        runner = CliRunner()

        with patch("stealthcrawler.cli.StealthCrawler") as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler_class.return_value = mock_crawler

            with patch("stealthcrawler.cli.asyncio.run") as mock_asyncio_run:
                mock_asyncio_run.return_value = {"https://example.com"}

                result = runner.invoke(
                    crawl,
                    ["https://example.com", "--exclude", "https://example.com/admin"],
                )

                assert result.exit_code == 0

                # Verify exclude parameter was parsed correctly
                mock_crawler_class.assert_called_once_with(
                    base=None,
                    exclude=["https://example.com/admin"],
                    save_html=False,
                    save_md=False,
                    urls_only=False,
                    output_dir="output",
                    headless=True,
                )

    def test_crawl_with_exclude_multiple(self):
        """Test crawl command with multiple exclude patterns."""
        runner = CliRunner()

        with patch("stealthcrawler.cli.StealthCrawler") as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler_class.return_value = mock_crawler

            with patch("stealthcrawler.cli.asyncio.run") as mock_asyncio_run:
                mock_asyncio_run.return_value = {"https://example.com"}

                result = runner.invoke(
                    crawl,
                    [
                        "https://example.com",
                        "--exclude",
                        "https://example.com/admin,https://example.com/private",
                    ],
                )

                assert result.exit_code == 0

                # Verify multiple exclude patterns were parsed correctly
                mock_crawler_class.assert_called_once_with(
                    base=None,
                    exclude=[
                        "https://example.com/admin",
                        "https://example.com/private",
                    ],
                    save_html=False,
                    save_md=False,
                    urls_only=False,
                    output_dir="output",
                    headless=True,
                )

    def test_crawl_with_exclude_empty_patterns(self):
        """Test crawl command with exclude patterns containing empty strings."""
        runner = CliRunner()

        with patch("stealthcrawler.cli.StealthCrawler") as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler_class.return_value = mock_crawler

            with patch("stealthcrawler.cli.asyncio.run") as mock_asyncio_run:
                mock_asyncio_run.return_value = {"https://example.com"}

                result = runner.invoke(
                    crawl,
                    [
                        "https://example.com",
                        "--exclude",
                        "https://example.com/admin, ,https://example.com/private, ",
                    ],
                )

                assert result.exit_code == 0

                # Verify empty patterns were filtered out
                mock_crawler_class.assert_called_once_with(
                    base=None,
                    exclude=[
                        "https://example.com/admin",
                        "https://example.com/private",
                    ],
                    save_html=False,
                    save_md=False,
                    urls_only=False,
                    output_dir="output",
                    headless=True,
                )

    def test_crawl_all_options(self):
        """Test crawl command with all options enabled."""
        runner = CliRunner()

        with patch("stealthcrawler.cli.StealthCrawler") as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler_class.return_value = mock_crawler

            with patch("stealthcrawler.cli.asyncio.run") as mock_asyncio_run:
                mock_asyncio_run.return_value = {
                    "https://example.com",
                    "https://example.com/page1",
                }

                result = runner.invoke(
                    crawl,
                    [
                        "https://example.com/start",
                        "--base",
                        "https://example.com",
                        "--exclude",
                        "https://example.com/admin,https://example.com/private",
                        "--save-html",
                        "--save-md",
                        "--output-dir",
                        "/custom/path",
                    ],
                )

                assert result.exit_code == 0

                # Verify all parameters were passed correctly
                mock_crawler_class.assert_called_once_with(
                    base="https://example.com",
                    exclude=[
                        "https://example.com/admin",
                        "https://example.com/private",
                    ],
                    save_html=True,
                    save_md=True,
                    urls_only=False,
                    output_dir="/custom/path",
                    headless=True,
                )

                assert "Successfully crawled 2 pages" in result.output
                assert "Content saved to:" in result.output

    def test_crawl_keyboard_interrupt(self):
        """Test handling of keyboard interrupt."""
        runner = CliRunner()

        with patch("stealthcrawler.cli.StealthCrawler") as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler_class.return_value = mock_crawler

            with patch("stealthcrawler.cli.asyncio.run") as mock_asyncio_run:
                mock_asyncio_run.side_effect = KeyboardInterrupt()

                result = runner.invoke(crawl, ["https://example.com"])

                # Should exit with abort code
                assert result.exit_code != 0

    def test_crawl_general_exception(self):
        """Test handling of general exceptions."""
        runner = CliRunner()

        with patch("stealthcrawler.cli.StealthCrawler") as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler_class.return_value = mock_crawler

            with patch("stealthcrawler.cli.asyncio.run") as mock_asyncio_run:
                mock_asyncio_run.side_effect = Exception("Something went wrong")

                result = runner.invoke(crawl, ["https://example.com"])

                # Should exit with error and show error message
                assert result.exit_code != 0
                assert "Error: Something went wrong" in result.output

    def test_crawl_empty_exclude(self):
        """Test crawl command with empty exclude parameter."""
        runner = CliRunner()

        with patch("stealthcrawler.cli.StealthCrawler") as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler_class.return_value = mock_crawler

            with patch("stealthcrawler.cli.asyncio.run") as mock_asyncio_run:
                mock_asyncio_run.return_value = {"https://example.com"}

                result = runner.invoke(crawl, ["https://example.com", "--exclude", ""])

                assert result.exit_code == 0

                # Empty exclude should result in None
                mock_crawler_class.assert_called_once_with(
                    base=None,
                    exclude=None,
                    save_html=False,
                    save_md=False,
                    urls_only=False,
                    output_dir="output",
                    headless=True,
                )

    def test_crawl_default_output_dir(self):
        """Test that default output directory is used when not specified."""
        runner = CliRunner()

        with patch("stealthcrawler.cli.StealthCrawler") as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler_class.return_value = mock_crawler

            with patch("stealthcrawler.cli.asyncio.run") as mock_asyncio_run:
                mock_asyncio_run.return_value = {"https://example.com"}

                result = runner.invoke(crawl, ["https://example.com"])

                assert result.exit_code == 0

                # Should use default output directory
                mock_crawler_class.assert_called_once_with(
                    base=None,
                    exclude=None,
                    save_html=False,
                    save_md=False,
                    urls_only=False,
                    output_dir="output",
                    headless=True,
                )


class TestCliMainGroup:
    """Test the main CLI group."""

    def test_main_group_help(self):
        """Test main group help text."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Stealth Crawler" in result.output
        assert "headless Chrome web crawler" in result.output

    def test_main_group_no_command(self):
        """Test main group without any command."""
        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code == 0
        # Should show usage information

    def test_crawl_subcommand_help(self):
        """Test crawl subcommand help text."""
        runner = CliRunner()
        result = runner.invoke(main, ["crawl", "--help"])

        assert result.exit_code == 0
        assert "Crawl a website" in result.output
        assert "--base" in result.output
        assert "--exclude" in result.output
        assert "--save-html" in result.output
        assert "--save-md" in result.output
        assert "--urls-only" in result.output
        assert "--output-dir" in result.output

    def test_invalid_subcommand(self):
        """Test handling of invalid subcommands."""
        runner = CliRunner()
        result = runner.invoke(main, ["invalid"])

        assert result.exit_code != 0
        # Should show error about invalid command


class TestCliOutputFormatting:
    """Test CLI output formatting."""

    def test_urls_only_output_sorted(self):
        """Test that URLs are output in sorted order for urls-only mode."""
        runner = CliRunner()

        with patch("stealthcrawler.cli.StealthCrawler") as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler_class.return_value = mock_crawler

            with patch("stealthcrawler.cli.asyncio.run") as mock_asyncio_run:
                # Return URLs in unsorted order
                mock_asyncio_run.return_value = {
                    "https://example.com/z-page",
                    "https://example.com/a-page",
                    "https://example.com/m-page",
                }

                result = runner.invoke(crawl, ["https://example.com", "--urls-only"])

                assert result.exit_code == 0

                # URLs should appear in sorted order in output
                lines = result.output.strip().split("\n")
                url_lines = [line for line in lines if line.startswith("https://")]

                expected_order = [
                    "https://example.com/a-page",
                    "https://example.com/m-page",
                    "https://example.com/z-page",
                ]

                assert url_lines == expected_order

    def test_content_saving_success_message(self):
        """Test success message formatting for content saving."""
        runner = CliRunner()

        with patch("stealthcrawler.cli.StealthCrawler") as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler_class.return_value = mock_crawler

            with patch("stealthcrawler.cli.asyncio.run") as mock_asyncio_run:
                mock_asyncio_run.return_value = {
                    "https://example.com",
                    "https://example.com/page1",
                    "https://example.com/page2",
                }

                with tempfile.TemporaryDirectory() as temp_dir:
                    result = runner.invoke(
                        crawl,
                        [
                            "https://example.com",
                            "--save-html",
                            "--output-dir",
                            temp_dir,
                        ],
                    )

                    assert result.exit_code == 0
                    assert "Successfully crawled 3 pages" in result.output
                    assert (
                        f"Content saved to: {Path(temp_dir).absolute()}"
                        in result.output
                    )

    def test_no_content_saving_no_path_message(self):
        """Test that no path message appears when not saving content."""
        runner = CliRunner()

        with patch("stealthcrawler.cli.StealthCrawler") as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler_class.return_value = mock_crawler

            with patch("stealthcrawler.cli.asyncio.run") as mock_asyncio_run:
                mock_asyncio_run.return_value = {"https://example.com"}

                result = runner.invoke(crawl, ["https://example.com"])

                assert result.exit_code == 0
                assert "Successfully crawled 1 pages" in result.output
                assert "Content saved to:" not in result.output
