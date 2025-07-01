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


async def GetPageHTML(
    page: pydoll.browser.page.Page,
    outputDir: Path,
    savePath: Path | str = None,
) -> None:
    if savePath is None:
        url = await page.current_url
        pageName = urlparse(url).path.strip("/").replace("/", "_") or "index"
        savePath = outputDir / f"{pageName}.html"
    if isinstance(savePath, str):
        savePath = Path(savePath)
    html = await page.page_source
    savePath.write_text(html, encoding="utf-8")


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
    url: str,
    base: list[str] | str,
    exclude: list[str] | str,
    initialOnly: bool,
    saveHtml: bool = False,
    outputDir: Path | str = Path("output"),
):

    if isinstance(base, str):

        base = [base]

    if isinstance(exclude, str):

        exclude = [exclude]

    if isinstance(outputDir, str):
        outputDir = Path(outputDir)

    outputDir.mkdir(parents=True, exist_ok=True)

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
            if saveHtml:
                await GetPageHTML(page, outputDir)

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
                        if saveHtml:
                            await GetPageHTML(page, outputDir)

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

    parser = argparse.ArgumentParser(description="Web Crawler")
    parser.add_argument("-u", "--url", help="URL to start at", required=True)
    parser.add_argument(
        "-b",
        "--base",
        help="Base path that all saved pages must start with.",
        default=None,
    )
    parser.add_argument(
        "-e",
        "--exclude",
        help="Comma-separated prefixes to skip",
        default="",
    )
    parser.add_argument(
        "--initial-only",
        action="store_true",
        help="Only collect links from the first page",
    )
    parser.add_argument(
        "--save-html",
        action="store_true",
        help="If set, save each crawled page's HTML to disk",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        help="Directory to write HTML files into",
        default="output",
    )

    args = parser.parse_args()
    url = args.url
    base = args.base or url
    exclude = [e.strip() for e in args.exclude.split(",") if e.strip()]
    initialOnly = args.initial_only
    saveHtml = args.save_html
    outputDir = Path(args.output_dir)
    outputDir.mkdir(parents=True, exist_ok=True)

    asyncio.run(
        Start(
            url=url,
            base=base,
            exclude=exclude,
            initialOnly=initialOnly,
            saveHtml=saveHtml,
            outputDir=outputDir,
        )
    )


if __name__ == "__main__":

    main()
