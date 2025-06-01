import argparse
import asyncio
import json
import os
from pathlib import Path
from urllib.parse import urlparse

import pydoll
from pydoll.browser.chrome import Chrome
from pydoll.browser.options import Options
from pydoll.constants import By


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


async def Start():

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")

    async with Chrome(options=options) as browser:

        await browser.start()
        page = await browser.get_page()

        await page.go_to("https://github.com/autoscrape-labs/pydoll")
        await page._wait_page_load()

        links = await GetPageSelfHRefs(page, buildURLs=True)

        Path("links.json").write_text(json.dumps(links, indent=4))


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

    asyncio.run(Start())


if __name__ == "__main__":

    main()
