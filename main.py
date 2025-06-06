import argparse
import asyncio
import json
import os
from collections import deque
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pydoll
import rich
from pydoll.browser.chrome import Chrome
from pydoll.browser.options import Options
from pydoll.constants import By
from rich.console import Console
from rich.layout import Layout
from rich.padding import Padding
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

console = Console()


async def GetPageScreenshot(
    page: pydoll.browser.page.Page, savePath: Path | str = None
) -> None:

    if savePath is None:

        url = await page.current_url
        pageName = urlparse(url).path.split("/")[-1]
        savePath = Path(f"{pageName}.png")

    if isinstance(savePath, str):

        savePath = Path(savePath)

    await page.get_screenshot(str(savePath))


async def GetPagePDF(
    page: pydoll.browser.page.Page, savePath: Path | str = None
) -> None:

    if savePath is None:

        url = await page.current_url
        pageName = urlparse(url).path.split("/")[-1]
        savePath = Path(f"{pageName}.pdf")

    if isinstance(savePath, str):

        savePath = Path(savePath)

    await page.print_to_pdf(str(savePath))


async def GetPageHRefs(page: pydoll.browser.page.Page) -> list[str]:

    refs = await page.find_elements(by=By.CSS_SELECTOR, value="[href]")

    hrefs = [element.get_attribute("href") for element in refs]

    return hrefs


async def GetPageSelfHRefs(
    page: pydoll.browser.page.Page, buildURLs: bool = True
) -> list[str]:
    """
    Get all hrefs that are relative to the current page URL.
    """

    hrefs = await GetPageHRefs(page)

    selfHRefs = [href for href in hrefs if href.startswith("/")]

    if buildURLs:

        pageURL = await page.current_url

        pageURL = urlparse(pageURL)

        baseURL = f"{pageURL.scheme}://{pageURL.netloc}"

        fullSelfHRefs = [f"{baseURL}{selfHRef}" for selfHRef in selfHRefs]

        return fullSelfHRefs

    else:

        return selfHRefs


async def Start(
    url: str, base: list[str] | str, exclude: list[str] | str, initialOnly: bool
):

    if isinstance(base, str):

        base = [base]

    if isinstance(exclude, str):

        exclude = [exclude]

    seen = set()
    stack = deque()

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")

    allLinks = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}", justify="left"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        BarColumn(bar_width=None),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
        expand=True,
    ) as progress:

        task = progress.add_task("Gathering URLs...", total=1)

        if len(url) > 40:

            displayUrl = f"{url[:20]}...{url[-20:]}"

        else:

            displayUrl = url

        progress.update(task, description=f"Scraping {displayUrl}", refresh=True)

        async with Chrome(options=options) as browser:

            await browser.start()
            page = await browser.get_page()

            await page.go_to(url)
            await page._wait_page_load()

            allLinks.append(url)

            links = await GetPageSelfHRefs(page, buildURLs=True)

            cleanedLinks = []

            for link in links:

                parsed = urlparse(link)

                # Drop the fragment (last part)
                urlWithoutFragment = urlunparse(parsed._replace(fragment=""))
                cleanedLinks.append(urlWithoutFragment)

            links = set(cleanedLinks)

            validSelfHRefs = {
                link
                for link in links
                if link.startswith(tuple(base))
                and not any(link.startswith(e) for e in exclude)
            }

            seen.add(url)

            stack.extend(validSelfHRefs)

            totalLinks = len(seen) + len(stack)

            progress.update(
                task,
                description=f"Scraped {displayUrl}",
                advance=1,
                total=totalLinks,
                refresh=True,
            )

            if initialOnly:

                Path("links.json").write_text(json.dumps(list(seen), indent=4))

                return list(validSelfHRefs)

            else:

                while stack:

                    url = stack.pop()

                    if len(url) > 40:

                        displayUrl = f"{url[:20]}...{url[-20:]}"

                    else:

                        displayUrl = url

                    if url.endswith(".zip"):

                        seen.add(url)

                        progress.update(
                            task,
                            description=f"Scraped {displayUrl}",
                            advance=1,
                            total=totalLinks,
                            refresh=True,
                        )

                    if url.endswith(".pdf"):

                        seen.add(url)

                        progress.update(
                            task,
                            description=f"Scraped {displayUrl}",
                            advance=1,
                            total=totalLinks,
                            refresh=True,
                        )

                    if url.endswith(".m3u8"):

                        seen.add(url)

                        progress.update(
                            task,
                            description=f"Scraped {displayUrl}",
                            advance=1,
                            total=totalLinks,
                            refresh=True,
                        )

                    if url not in seen:

                        progress.update(
                            task, description=f"Scraping {displayUrl}", refresh=True
                        )

                        await page.go_to(url)
                        await page._wait_page_load()

                        allLinks.append(url)

                        Path("allLinks.json").write_text(
                            json.dumps(list(allLinks), indent=4)
                        )

                        links = await GetPageSelfHRefs(page, buildURLs=True)

                        cleanedLinks = []

                        for link in links:

                            parsed = urlparse(link)

                            # Drop the fragment (last part)
                            urlWithoutFragment = urlunparse(
                                parsed._replace(fragment="")
                            )
                            cleanedLinks.append(urlWithoutFragment)

                        links = set(cleanedLinks)

                        validSelfHRefs = {
                            link
                            for link in links
                            if link.startswith(tuple(base))
                            and not any(link.startswith(e) for e in exclude)
                        }

                        newUrls = set(validSelfHRefs) - set(seen) - set(stack)

                        stack.extend(newUrls)

                        totalLinks = len(seen) + len(stack)

                        seen.add(url)

                        Path("links.json").write_text(json.dumps(list(seen), indent=4))

                        progress.update(
                            task,
                            description=f"Scraped {displayUrl}",
                            advance=1,
                            total=totalLinks,
                            refresh=True,
                        )

                return seen


def main():

    # parser = argparse.ArgumentParser(description=f"Web Crawler")

    # parser.add_argument("-u", "--url", help="URL to start at", required=True)
    # parser.add_argument(
    #     "-b",
    #     "--base",
    #     help="Base path that all pages that are saved must start with. Default to given url from --url.",
    #     required=False,
    #     default=None,
    # )

    # parser.add_argument("i", "initial_only", help="Only get links from the given url", default=False)

    # args = parser.parse_args()

    # url = args.url

    # base = args.base if args.base else url

    url = "https://developer.apple.com/documentation/eventkit"

    base = "https://developer.apple.com/documentation/eventkit"

    exclude = []

    initialOnly = False

    asyncio.run(Start(url=url, base=base, exclude=exclude, initialOnly=initialOnly))


if __name__ == "__main__":

    main()
