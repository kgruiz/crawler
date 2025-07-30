"""Command-line interface for the stealth crawler."""

import asyncio
from pathlib import Path

import click

from .core import StealthCrawler


@click.group()
def main():
    """Stealth Crawler - A headless Chrome web crawler."""
    pass


@main.command()
@click.argument("url")
@click.option(
    "--base",
    help="Base URL(s) that crawled URLs must start with (defaults to start URL)",
)
@click.option("--exclude", help="Comma-separated URL prefixes to exclude from crawling")
@click.option("--save-html", is_flag=True, help="Save each crawled page as HTML")
@click.option("--save-md", is_flag=True, help="Save each crawled page as Markdown")
@click.option(
    "--urls-only", is_flag=True, help="Only discover URLs without saving content"
)
@click.option("--output-dir", default="output", help="Directory to save content in")
def crawl(url, base, exclude, save_html, save_md, urls_only, output_dir):
    """Crawl a website starting from the given URL."""
    try:
        # Parse exclude patterns
        exclude_list = None
        if exclude:
            exclude_list = [e.strip() for e in exclude.split(",") if e.strip()]

        # Create crawler instance
        crawler = StealthCrawler(
            base=base,
            exclude=exclude_list,
            save_html=save_html,
            save_md=save_md,
            urls_only=urls_only,
            output_dir=output_dir,
            headless=True,
        )

        # Run the crawl
        discovered_urls = asyncio.run(crawler.crawl(url))

        # Handle output
        if urls_only:
            # Print newline-separated URLs
            for discovered_url in sorted(discovered_urls):
                click.echo(discovered_url)
        else:
            click.echo(f"Successfully crawled {len(discovered_urls)} pages")
            if save_html or save_md:
                click.echo(f"Content saved to: {Path(output_dir).absolute()}")

    except KeyboardInterrupt:
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":

    main()
