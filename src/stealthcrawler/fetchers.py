"""Async helpers for saving page content."""

from pathlib import Path

import html2text
import pydoll

from .utils import safe_filename


async def save_html(page, out_dir: Path) -> None:
    """Save page HTML content to file.

    Args:
        page: The browser page to save
        out_dir: Output directory to save HTML file in
    """
    # Handle both property access and coroutine cases for testing
    url = page.current_url
    if hasattr(url, "__await__"):
        url = await url
    filename = safe_filename(url, ".html")
    save_path = out_dir / filename

    # Handle both property access and coroutine cases for testing
    html = page.page_source
    if hasattr(html, "__await__"):
        html = await html
    save_path.write_text(html, encoding="utf-8")


async def save_markdown(page, out_dir: Path) -> None:
    """Save page content as Markdown using html2text.

    Args:
        page: The browser page to save
        out_dir: Output directory to save Markdown file in
    """
    # Handle both property access and coroutine cases for testing
    url = page.current_url
    if hasattr(url, "__await__"):
        url = await url
    filename = safe_filename(url, ".md")
    save_path = out_dir / filename

    # Handle both property access and coroutine cases for testing
    html = page.page_source
    if hasattr(html, "__await__"):
        html = await html
    markdown = html2text.html2text(html)
    save_path.write_text(markdown, encoding="utf-8")


async def save_pdf(page, path: Path) -> None:
    """Save page as PDF file.

    Args:
        page: The browser page to save
        path: Full path where to save the PDF file
    """
    await page.print_to_pdf(str(path))


async def save_screenshot(page, path: Path) -> None:
    """Save page screenshot as PNG file.

    Args:
        page: The browser page to save
        path: Full path where to save the screenshot file
    """
    await page.get_screenshot(str(path))
