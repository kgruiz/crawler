"""Stealth Crawler - A headless Chrome web crawler."""

import asyncio

try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version

from .core import StealthCrawler

__version__ = version("stealth-crawler")
__all__ = ["StealthCrawler", "crawl"]


def crawl(url: str, **kwargs) -> set[str]:
    """Crawl a website starting from the given URL.

    This is a convenience function that creates a StealthCrawler instance
    and runs the crawl synchronously.

    Args:
        url: The URL to start crawling from
        **kwargs: Additional arguments to pass to StealthCrawler

    Returns:
        Set of all discovered URLs
    """

    return asyncio.run(StealthCrawler(**kwargs).crawl(url))
