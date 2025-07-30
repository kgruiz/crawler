"""URL parsing and extraction functions."""

from urllib.parse import urlparse, urlunparse

import pydoll
from pydoll.constants import By

from .utils import normalize_url


async def get_hrefs(page: pydoll.browser.page.Page) -> list[str]:
    """Get all href attributes from anchor tags on the page.

    Args:
        page: The browser page to extract hrefs from

    Returns:
        List of href URLs found on the page
    """
    refs = await page.find_elements(by=By.CSS_SELECTOR, value="[href]")
    hrefs = [element.get_attribute("href") for element in refs]
    return hrefs


async def get_self_hrefs(
    page: pydoll.browser.page.Page, build_absolute: bool = True
) -> list[str]:
    """Get all href attributes that start with '/' (relative to current domain).

    Args:
        page: The browser page to extract hrefs from
        build_absolute: If True, prepend scheme+host to build absolute URLs

    Returns:
        List of relative href URLs, optionally converted to absolute URLs
    """
    hrefs = await get_hrefs(page)

    # Keep only links that start with '/'
    self_hrefs = [href for href in hrefs if href.startswith("/")]

    if build_absolute:
        page_url = await page.current_url
        parsed = urlparse(page_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        full_self_hrefs = [f"{base_url}{self_href}" for self_href in self_hrefs]
        return [normalize_url(url) for url in full_self_hrefs]
    else:
        return [normalize_url(url) for url in self_hrefs]
