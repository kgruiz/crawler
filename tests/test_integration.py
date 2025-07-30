"""Integration tests for the stealth crawler."""

import asyncio
import shutil
import tempfile
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from stealthcrawler import StealthCrawler


class TestStealthCrawlerIntegration(AioHTTPTestCase):
    """Integration test using a test HTTP server."""

    async def get_application(self):
        """Create test web application."""
        app = web.Application()

        # Test pages with links
        async def index(request):
            return web.Response(
                text="""
                <html>
                <body>
                    <h1>Test Index</h1>
                    <a href="/page1">Page 1</a>
                    <a href="/page2">Page 2</a>
                    <a href="https://external.com/page">External</a>
                </body>
                </html>
                """,
                content_type="text/html",
            )

        async def page1(request):
            return web.Response(
                text="""
                <html>
                <body>
                    <h1>Page 1</h1>
                    <a href="/page2">Page 2</a>
                    <a href="/subpage">Subpage</a>
                </body>
                </html>
                """,
                content_type="text/html",
            )

        async def page2(request):
            return web.Response(
                text="""
                <html>
                <body>
                    <h1>Page 2</h1>
                    <a href="/page1">Back to Page 1</a>
                </body>
                </html>
                """,
                content_type="text/html",
            )

        async def subpage(request):
            return web.Response(
                text="""
                <html>
                <body>
                    <h1>Subpage</h1>
                    <p>This is a subpage</p>
                </body>
                </html>
                """,
                content_type="text/html",
            )

        app.router.add_get("/", index)
        app.router.add_get("/page1", page1)
        app.router.add_get("/page2", page2)
        app.router.add_get("/subpage", subpage)

        return app

    @unittest_run_loop
    async def test_urls_only_crawl(self):
        """Test crawling with urls_only=True."""
        # Get the test server URL
        base_url = f"http://127.0.0.1:{self.server.port}"

        # Create crawler
        crawler = StealthCrawler(urls_only=True)

        # Run crawl
        discovered_urls = await crawler.crawl(base_url)

        # Verify discovered URLs
        expected_urls = {
            base_url,
            f"{base_url}/page1",
            f"{base_url}/page2",
            f"{base_url}/subpage",
        }

        assert discovered_urls == expected_urls

    @unittest_run_loop
    async def test_content_saving_crawl(self):
        """Test crawling with content saving."""
        # Get the test server URL
        base_url = f"http://127.0.0.1:{self.server.port}"

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create crawler with content saving
            crawler = StealthCrawler(
                save_html=True, save_md=True, output_dir=temp_dir, urls_only=False
            )

            # Run crawl
            discovered_urls = await crawler.crawl(base_url)

            # Verify discovered URLs
            expected_urls = {
                base_url,
                f"{base_url}/page1",
                f"{base_url}/page2",
                f"{base_url}/subpage",
            }
            assert discovered_urls == expected_urls

            # Verify files were created
            output_path = Path(temp_dir)
            html_dir = output_path / "html"
            md_dir = output_path / "markdown"

            assert html_dir.exists()
            assert md_dir.exists()

            # Check that some files were created
            html_files = list(html_dir.glob("*.html"))
            md_files = list(md_dir.glob("*.md"))

            assert len(html_files) > 0
            assert len(md_files) > 0
