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


async def Scrape():

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")

    async with Chrome(options=options) as browser:

        await browser.start()
        page = await browser.get_page()
        print(type(page))
        await page.go_to("https://github.com/autoscrape-labs/pydoll")


def main():

    asyncio.run(Scrape())


if __name__ == "__main__":

    main()
