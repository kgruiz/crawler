"""Tests for URL parsing functions."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from stealthcrawler.parsers import get_hrefs, get_self_hrefs


class TestGetHrefs:
    """Test get_hrefs function."""

    @pytest.mark.asyncio
    async def test_get_hrefs(self):
        """Test basic href extraction."""
        # Mock page and elements
        page = AsyncMock()

        # Mock elements with href attributes
        element1 = MagicMock()
        element1.get_attribute.return_value = "https://example.com/page1"
        element2 = MagicMock()
        element2.get_attribute.return_value = "/relative/page"
        element3 = MagicMock()
        element3.get_attribute.return_value = "https://other.com/external"

        page.find_elements.return_value = [element1, element2, element3]

        result = await get_hrefs(page)

        expected = [
            "https://example.com/page1",
            "/relative/page",
            "https://other.com/external",
        ]
        assert result == expected


class TestGetSelfHrefs:
    """Test get_self_hrefs function."""

    @pytest.mark.asyncio
    async def test_get_self_hrefs_relative(self):
        """Test extraction of relative hrefs only."""
        # Mock page and elements
        page = AsyncMock()

        # Mock elements with mixed href types
        element1 = MagicMock()
        element1.get_attribute.return_value = "https://example.com/page1"
        element2 = MagicMock()
        element2.get_attribute.return_value = "/relative/page"
        element3 = MagicMock()
        element3.get_attribute.return_value = "/another/relative"
        element4 = MagicMock()
        element4.get_attribute.return_value = "https://other.com/external"

        page.find_elements.return_value = [element1, element2, element3, element4]

        result = await get_self_hrefs(page, build_absolute=False)

        expected = ["/relative/page", "/another/relative"]
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_self_hrefs_absolute(self):
        """Test conversion to absolute URLs."""
        # Mock page and elements
        page = AsyncMock()
        page.current_url = "https://example.com/current/page"

        # Mock elements with relative hrefs
        element1 = MagicMock()
        element1.get_attribute.return_value = "/relative/page"
        element2 = MagicMock()
        element2.get_attribute.return_value = "/another/relative"

        page.find_elements.return_value = [element1, element2]

        result = await get_self_hrefs(page, build_absolute=True)

        expected = [
            "https://example.com/relative/page",
            "https://example.com/another/relative",
        ]
        assert result == expected
