"""Core StealthCrawler class implementation."""

from collections import deque
from pathlib import Path

import pydoll
from pydoll.browser.chrome import Chrome
from pydoll.browser.options import Options

from .fetchers import save_html, save_markdown
from .parsers import get_self_hrefs
from .progress import make_progress
from .utils import ensure_dir, normalize_url


class StealthCrawler:
    """A stealth web crawler using headless Chrome."""

    def __init__(
        self,
        base: str | list[str] = None,
        exclude: str | list[str] = None,
        save_html: bool = False,
        save_md: bool = False,
        urls_only: bool = False,
        output_dir: str = "output",
        headless: bool = True,
    ):
        """Initialize the StealthCrawler.

        Args:
            base: Base URL(s) that crawled URLs must start with
            exclude: URL prefix(es) to exclude from crawling
            save_html: Whether to save HTML content
            save_md: Whether to save Markdown content
            urls_only: If True, only discover URLs without saving content
            output_dir: Directory to save content in
            headless: Whether to run Chrome in headless mode
        """
        # Normalize base and exclude to lists
        if isinstance(base, str):
            self.base = [base]
        elif base is None:
            self.base = []
        else:
            self.base = list(base)

        if isinstance(exclude, str):
            self.exclude = [exclude]
        elif exclude is None:
            self.exclude = []
        else:
            self.exclude = list(exclude)

        self.save_html = save_html
        self.save_md = save_md
        self.urls_only = urls_only
        self.output_dir = Path(output_dir)
        self.headless = headless

        # Internal tracking
        self._seen: set[str] = set()
        self._stack: deque[str] = deque()

    async def crawl(self, start_url: str) -> set[str]:
        """Crawl starting from the given URL.

        Args:
            start_url: The URL to start crawling from

        Returns:
            Set of all discovered URLs
        """
        # If base is not set, use the start_url as base
        if not self.base:
            self.base = [start_url]

        # Prepare output directories unless urls_only
        if not self.urls_only:
            ensure_dir(self.output_dir)

            if self.save_html and self.save_md:
                self.html_dir = self.output_dir / "html"
                self.md_dir = self.output_dir / "markdown"
                ensure_dir(self.html_dir)
                ensure_dir(self.md_dir)
            else:
                self.html_dir = self.md_dir = self.output_dir

        # Setup Chrome options
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")

        with make_progress() as progress:
            if self.urls_only:
                task = progress.add_task("Discovering URLs...", total=1)
            else:
                task = progress.add_task("Gathering URLs...", total=1)

            display_url = self._truncate_url(start_url)
            action = "Discovering URLs from" if self.urls_only else "Scraping"
            progress.update(task, description=f"{action} {display_url}", refresh=True)

            async with Chrome(options=options) as browser:
                await browser.start()
                page = await browser.get_page()

                # Process the start URL
                await self._process_page(page, start_url, progress, task)

                # Process all URLs in the stack
                while self._stack:
                    url = self._stack.pop()

                    if url in self._seen:
                        continue

                    # Skip certain file types
                    if url.endswith((".zip", ".pdf", ".m3u8")):
                        self._seen.add(url)
                        display_url = self._truncate_url(url)
                        action = "Discovered URLs from" if self.urls_only else "Scraped"
                        progress.update(
                            task,
                            description=f"{action} {display_url}",
                            advance=1,
                            total=len(self._seen) + len(self._stack),
                            refresh=True,
                        )
                        continue

                    await self._process_page(page, url, progress, task)

                return self._seen

    async def _process_page(
        self, page: pydoll.browser.page.Page, url: str, progress, task_id
    ) -> None:
        """Process a single page: visit, save content, extract links.

        Args:
            page: The browser page object
            url: URL to process
            progress: Progress bar instance
            task_id: Progress task ID
        """
        display_url = self._truncate_url(url)
        action = "Discovering URLs from" if self.urls_only else "Scraping"
        progress.update(task_id, description=f"{action} {display_url}", refresh=True)

        # Navigate to the page
        await page.go_to(url)
        await page._wait_page_load()

        # Save content if not urls_only
        if not self.urls_only:
            if self.save_html:
                await save_html(page, self.html_dir)
            if self.save_md:
                await save_markdown(page, self.md_dir)

        # Mark as seen
        self._seen.add(url)

        # Extract and filter links
        links = await get_self_hrefs(page, build_absolute=True)
        valid_links = self._filter_links(links)

        # Add new links to stack
        new_urls = set(valid_links) - self._seen - set(self._stack)
        self._stack.extend(new_urls)

        # Update progress
        total_links = len(self._seen) + len(self._stack)
        action = "Discovered URLs from" if self.urls_only else "Scraped"
        progress.update(
            task_id,
            description=f"{action} {display_url}",
            advance=1,
            total=total_links,
            refresh=True,
        )

    def _filter_links(self, links: list[str]) -> list[str]:
        """Filter links based on base and exclude patterns.

        Args:
            links: List of URLs to filter

        Returns:
            Filtered list of valid URLs
        """
        valid_links = []
        for link in links:
            normalized = normalize_url(link)
            # Check if link starts with any base URL
            if self.base and not any(normalized.startswith(base) for base in self.base):
                continue
            # Check if link starts with any exclude pattern
            if self.exclude and any(
                normalized.startswith(exclude) for exclude in self.exclude
            ):
                continue
            valid_links.append(normalized)

        return valid_links

    def _truncate_url(self, url: str) -> str:
        """Truncate URL for display purposes.

        Args:
            url: URL to truncate

        Returns:
            Truncated URL string
        """
        if len(url) > 40:
            return f"{url[:20]}...{url[-20:]}"
        return url
