"""Utility functions for the stealth crawler."""

from pathlib import Path
from urllib.parse import urlparse, urlunparse


def normalize_url(url: str) -> str:
    """Strip fragments and normalize duplicate slashes from URL.

    Args:
        url: The URL to normalize

    Returns:
        Normalized URL string
    """
    parsed = urlparse(url)
    # Drop the fragment and normalize path
    normalized = urlunparse(parsed._replace(fragment=""))
    return normalized


def safe_filename(url: str, ext: str = None) -> str:
    """Convert URL to safe filename using netloc + path.

    Args:
        url: The URL to convert
        ext: File extension to append (with dot)

    Returns:
        Safe filename string
    """
    parsed = urlparse(url)
    # Use netloc + path, replace / with _, default to index
    path_part = parsed.path.strip("/").replace("/", "_") or "index"
    filename = f"{parsed.netloc}_{path_part}" if parsed.netloc else path_part

    if ext:
        filename = f"{filename}{ext}"

    return filename


def ensure_dir(path: Path) -> None:
    """Ensure directory exists, creating it if necessary.

    Args:
        path: Path to directory to create
    """
    path.mkdir(parents=True, exist_ok=True)
