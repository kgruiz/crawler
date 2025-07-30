"""URL parsing and extraction functions."""

from urllib.parse import urlparse, urlunparse

import pydoll
from pydoll.constants import By

from .utils import normalize_url


async def get_hrefs(page) -> list[str]:
    """Get all href attributes from anchor tags on the page.

    Args:
        page: The browser page to extract hrefs from

    Returns:
        List of href URLs found on the page
    """
    refs = await page.query("a[href]")
    # Handle both single element and list returns
    if not isinstance(refs, list):
        refs = [refs] if refs is not None else []
    hrefs = [element.get_attribute("href") for element in refs]
    # Filter out None values
    return [href for href in hrefs if href is not None]


async def get_self_hrefs(page, build_absolute: bool = True) -> list[str]:
    """Get all href attributes that are relative to current domain.

    Args:
        page: The browser page to extract hrefs from
        build_absolute: If True, prepend scheme+host to build absolute URLs

    Returns:
        List of relative href URLs, optionally converted to absolute URLs
    """
    hrefs = await get_hrefs(page)

    # Keep only relative links (not absolute URLs)
    def is_relative(href):
        """Check if href is relative (not an absolute URL)."""
        return not (
            href.startswith("http://")
            or href.startswith("https://")
            or href.startswith("//")
            or href.startswith("data:")
            or href.startswith("mailto:")
            or href.startswith("tel:")
        )

    self_hrefs = [href for href in hrefs if is_relative(href)]

    if build_absolute:
        # Handle both property access and coroutine cases for testing
        page_url = page.current_url
        if hasattr(page_url, "__await__"):
            page_url = await page_url

        parsed = urlparse(page_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        full_self_hrefs = [f"{base_url}{self_href}" for self_href in self_hrefs]
        return [normalize_url(url) for url in full_self_hrefs]
    else:
        # Don't normalize fragment-only and query-only URLs
        result = []
        for href in self_hrefs:
            if href.startswith("#") or href.startswith("?"):
                result.append(href)
            else:
                result.append(normalize_url(href))
        return result
