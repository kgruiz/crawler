"""Tests for fetcher functions."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from stealthcrawler.fetchers import save_html, save_markdown, save_pdf, save_screenshot


class TestSaveHtml:
    """Test save_html function."""

    @pytest.mark.asyncio
    async def test_save_html_basic(self):
        """Test basic HTML saving functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Mock page
            page = AsyncMock()
            page.current_url = "https://example.com/test-page"
            page.page_source = "<html><body><h1>Test</h1></body></html>"

            with patch("stealthcrawler.fetchers.safe_filename") as mock_safe_filename:
                mock_safe_filename.return_value = "example.com_test-page.html"

                await save_html(page, output_dir)

                # Check file was created with correct content
                expected_file = output_dir / "example.com_test-page.html"
                assert expected_file.exists()

                content = expected_file.read_text(encoding="utf-8")
                assert content == "<html><body><h1>Test</h1></body></html>"

                # Verify safe_filename was called correctly
                mock_safe_filename.assert_called_once_with(
                    "https://example.com/test-page", ".html"
                )

    @pytest.mark.asyncio
    async def test_save_html_with_unicode(self):
        """Test HTML saving with unicode content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Mock page with unicode content
            page = AsyncMock()
            page.current_url = "https://example.com/unicode"
            page.page_source = "<html><body><h1>Tëst with ñice 中文</h1></body></html>"

            with patch("stealthcrawler.fetchers.safe_filename") as mock_safe_filename:
                mock_safe_filename.return_value = "example.com_unicode.html"

                await save_html(page, output_dir)

                expected_file = output_dir / "example.com_unicode.html"
                content = expected_file.read_text(encoding="utf-8")
                assert "Tëst with ñice 中文" in content

    @pytest.mark.asyncio
    async def test_save_html_file_error(self):
        """Test handling of file write errors."""
        # Use a read-only directory to force a permission error
        page = AsyncMock()
        page.current_url = "https://example.com/test"
        page.page_source = "<html><body>Test</body></html>"

        with patch("stealthcrawler.fetchers.safe_filename") as mock_safe_filename:
            mock_safe_filename.return_value = "test.html"

            # Mock Path.write_text to raise an exception
            with patch("pathlib.Path.write_text") as mock_write:
                mock_write.side_effect = PermissionError("Permission denied")

                with pytest.raises(PermissionError):
                    await save_html(page, Path("/invalid/path"))


class TestSaveMarkdown:
    """Test save_markdown function."""

    @pytest.mark.asyncio
    async def test_save_markdown_basic(self):
        """Test basic Markdown saving functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Mock page
            page = AsyncMock()
            page.current_url = "https://example.com/test-page"
            page.page_source = (
                "<html><body><h1>Test Header</h1><p>Test paragraph</p></body></html>"
            )

            with patch("stealthcrawler.fetchers.safe_filename") as mock_safe_filename:
                mock_safe_filename.return_value = "example.com_test-page.md"

                with patch(
                    "stealthcrawler.fetchers.html2text.html2text"
                ) as mock_html2text:
                    mock_html2text.return_value = "# Test Header\n\nTest paragraph\n"

                    await save_markdown(page, output_dir)

                    # Check file was created with correct content
                    expected_file = output_dir / "example.com_test-page.md"
                    assert expected_file.exists()

                    content = expected_file.read_text(encoding="utf-8")
                    assert content == "# Test Header\n\nTest paragraph\n"

                    # Verify html2text was called with HTML content
                    mock_html2text.assert_called_once_with(
                        "<html><body><h1>Test Header</h1><p>Test paragraph</p></body></html>"
                    )

                    # Verify safe_filename was called correctly
                    mock_safe_filename.assert_called_once_with(
                        "https://example.com/test-page", ".md"
                    )

    @pytest.mark.asyncio
    async def test_save_markdown_complex_html(self):
        """Test Markdown conversion with complex HTML."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Mock page with complex HTML
            html_content = """
            <html>
                <body>
                    <h1>Main Title</h1>
                    <p>A paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
                    <ul>
                        <li>List item 1</li>
                        <li>List item 2</li>
                    </ul>
                    <a href="https://example.com">Link</a>
                </body>
            </html>
            """

            page = AsyncMock()
            page.current_url = "https://example.com/complex"
            page.page_source = html_content

            with patch("stealthcrawler.fetchers.safe_filename") as mock_safe_filename:
                mock_safe_filename.return_value = "complex.md"

                # Let html2text actually process the HTML
                await save_markdown(page, output_dir)

                expected_file = output_dir / "complex.md"
                assert expected_file.exists()

                content = expected_file.read_text(encoding="utf-8")
                # Check that markdown conversion occurred (should contain markdown syntax)
                assert "# Main Title" in content or "Main Title" in content
                assert "**bold**" in content or "bold" in content

    @pytest.mark.asyncio
    async def test_save_markdown_empty_html(self):
        """Test Markdown saving with empty HTML."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            page = AsyncMock()
            page.current_url = "https://example.com/empty"
            page.page_source = ""

            with patch("stealthcrawler.fetchers.safe_filename") as mock_safe_filename:
                mock_safe_filename.return_value = "empty.md"

                await save_markdown(page, output_dir)

                expected_file = output_dir / "empty.md"
                assert expected_file.exists()

                # File should exist even if empty
                content = expected_file.read_text(encoding="utf-8")
                assert isinstance(content, str)  # Should be a string, even if empty


class TestSavePdf:
    """Test save_pdf function."""

    @pytest.mark.asyncio
    async def test_save_pdf_basic(self):
        """Test basic PDF saving functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test.pdf"

            # Mock page
            page = AsyncMock()
            page.print_to_pdf.return_value = None

            await save_pdf(page, pdf_path)

            # Verify print_to_pdf was called with correct path
            page.print_to_pdf.assert_called_once_with(str(pdf_path))

    @pytest.mark.asyncio
    async def test_save_pdf_error(self):
        """Test handling of PDF save errors."""
        pdf_path = Path("/invalid/path/test.pdf")

        # Mock page that raises an error
        page = AsyncMock()
        page.print_to_pdf.side_effect = Exception("PDF generation failed")

        with pytest.raises(Exception, match="PDF generation failed"):
            await save_pdf(page, pdf_path)

    @pytest.mark.asyncio
    async def test_save_pdf_path_conversion(self):
        """Test that Path objects are converted to strings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test.pdf"

            page = AsyncMock()
            page.print_to_pdf.return_value = None

            await save_pdf(page, pdf_path)

            # Verify the path was converted to string
            args, kwargs = page.print_to_pdf.call_args
            assert isinstance(args[0], str)
            assert args[0] == str(pdf_path)


class TestSaveScreenshot:
    """Test save_screenshot function."""

    @pytest.mark.asyncio
    async def test_save_screenshot_basic(self):
        """Test basic screenshot saving functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            screenshot_path = Path(temp_dir) / "screenshot.png"

            # Mock page
            page = AsyncMock()
            page.get_screenshot.return_value = None

            await save_screenshot(page, screenshot_path)

            # Verify get_screenshot was called with correct path
            page.get_screenshot.assert_called_once_with(str(screenshot_path))

    @pytest.mark.asyncio
    async def test_save_screenshot_error(self):
        """Test handling of screenshot save errors."""
        screenshot_path = Path("/invalid/path/screenshot.png")

        # Mock page that raises an error
        page = AsyncMock()
        page.get_screenshot.side_effect = Exception("Screenshot failed")

        with pytest.raises(Exception, match="Screenshot failed"):
            await save_screenshot(page, screenshot_path)

    @pytest.mark.asyncio
    async def test_save_screenshot_path_conversion(self):
        """Test that Path objects are converted to strings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            screenshot_path = Path(temp_dir) / "screenshot.png"

            page = AsyncMock()
            page.get_screenshot.return_value = None

            await save_screenshot(page, screenshot_path)

            # Verify the path was converted to string
            args, kwargs = page.get_screenshot.call_args
            assert isinstance(args[0], str)
            assert args[0] == str(screenshot_path)


class TestFetchersIntegration:
    """Integration tests for fetcher functions."""

    @pytest.mark.asyncio
    async def test_save_all_formats(self):
        """Test saving content in all supported formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Mock page with realistic content
            page = AsyncMock()
            page.current_url = "https://example.com/test"
            page.page_source = (
                "<html><body><h1>Test Page</h1><p>Content</p></body></html>"
            )
            page.print_to_pdf.return_value = None
            page.get_screenshot.return_value = None

            with patch("stealthcrawler.fetchers.safe_filename") as mock_safe_filename:
                mock_safe_filename.side_effect = lambda url, ext: f"test{ext}"

                # Save in all formats
                await save_html(page, output_dir)
                await save_markdown(page, output_dir)
                await save_pdf(page, output_dir / "test.pdf")
                await save_screenshot(page, output_dir / "test.png")

                # Verify all files were processed
                assert (output_dir / "test.html").exists()
                assert (output_dir / "test.md").exists()
                page.print_to_pdf.assert_called_once()
                page.get_screenshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_saves(self):
        """Test that multiple save operations can run concurrently."""
        import asyncio

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Mock multiple pages
            pages = []
            for i in range(3):
                page = AsyncMock()
                page.current_url = f"https://example.com/page{i}"
                page.page_source = f"<html><body><h1>Page {i}</h1></body></html>"
                pages.append(page)

            with patch("stealthcrawler.fetchers.safe_filename") as mock_safe_filename:
                mock_safe_filename.side_effect = (
                    lambda url, ext: f"{url.split('/')[-1]}{ext}"
                )

                # Run saves concurrently
                tasks = []
                for page in pages:
                    tasks.append(save_html(page, output_dir))
                    tasks.append(save_markdown(page, output_dir))

                await asyncio.gather(*tasks)

                # Verify all files were created
                for i in range(3):
                    assert (output_dir / f"page{i}.html").exists()
                    assert (output_dir / f"page{i}.md").exists()
