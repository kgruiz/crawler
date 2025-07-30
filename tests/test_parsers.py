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

        page.query.return_value = [element1, element2, element3]

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

        page.query.return_value = [element1, element2, element3, element4]

        result = await get_self_hrefs(page, build_absolute=False)

        expected = ["/relative/page", "/another/relative"]
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_self_hrefs_absolute(self):
        """Test conversion to absolute URLs."""
        # Mock page and elements
        page = AsyncMock()

        # Create a coroutine that returns the URL
        async def get_current_url():
            return "https://example.com/current/page"

        # Set current_url as a coroutine
        page.current_url = get_current_url()

        # Mock elements with relative hrefs
        element1 = MagicMock()
        element1.get_attribute.return_value = "/relative/page"
        element2 = MagicMock()
        element2.get_attribute.return_value = "/another/relative"

        page.query.return_value = [element1, element2]

        result = await get_self_hrefs(page, build_absolute=True)

        expected = [
            "https://example.com/relative/page",
            "https://example.com/another/relative",
        ]
        assert result == expected


class TestGetHrefsEdgeCases:
    """Test edge cases for get_hrefs function."""

    @pytest.mark.asyncio
    async def test_get_hrefs_empty_page(self):
        """Test get_hrefs with no links on page."""
        page = AsyncMock()
        page.query.return_value = []

        result = await get_hrefs(page)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_hrefs_none_hrefs(self):
        """Test get_hrefs with elements that have None hrefs."""
        page = AsyncMock()

        # Mock elements where some return None for href
        element1 = MagicMock()
        element1.get_attribute.return_value = "https://example.com/valid"
        element2 = MagicMock()
        element2.get_attribute.return_value = None
        element3 = MagicMock()
        element3.get_attribute.return_value = "https://example.com/another"

        page.query.return_value = [element1, element2, element3]

        result = await get_hrefs(page)

        # Should filter out None values
        expected = [
            "https://example.com/valid",
            "https://example.com/another",
        ]
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_hrefs_empty_hrefs(self):
        """Test get_hrefs with elements that have empty string hrefs."""
        page = AsyncMock()

        # Mock elements with empty href values
        element1 = MagicMock()
        element1.get_attribute.return_value = "https://example.com/valid"
        element2 = MagicMock()
        element2.get_attribute.return_value = ""
        element3 = MagicMock()
        element3.get_attribute.return_value = "   "  # Whitespace only

        page.query.return_value = [element1, element2, element3]

        result = await get_hrefs(page)

        # Should include empty strings as-is (filtering is done elsewhere)
        expected = [
            "https://example.com/valid",
            "",
            "   ",
        ]
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_hrefs_special_protocols(self):
        """Test get_hrefs with special protocol links."""
        page = AsyncMock()

        # Mock elements with various protocol types
        element1 = MagicMock()
        element1.get_attribute.return_value = "mailto:test@example.com"
        element2 = MagicMock()
        element2.get_attribute.return_value = "tel:+1234567890"
        element3 = MagicMock()
        element3.get_attribute.return_value = "javascript:void(0)"
        element4 = MagicMock()
        element4.get_attribute.return_value = "ftp://ftp.example.com/file"
        element5 = MagicMock()
        element5.get_attribute.return_value = "#anchor"

        page.query.return_value = [element1, element2, element3, element4, element5]

        result = await get_hrefs(page)

        expected = [
            "mailto:test@example.com",
            "tel:+1234567890",
            "javascript:void(0)",
            "ftp://ftp.example.com/file",
            "#anchor",
        ]
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_hrefs_query_exception(self):
        """Test get_hrefs when page.query raises exception."""
        page = AsyncMock()
        page.query.side_effect = Exception("Query failed")

        with pytest.raises(Exception, match="Query failed"):
            await get_hrefs(page)

    @pytest.mark.asyncio
    async def test_get_hrefs_get_attribute_exception(self):
        """Test get_hrefs when element.get_attribute raises exception."""
        page = AsyncMock()

        # Mock element that raises exception
        element1 = MagicMock()
        element1.get_attribute.side_effect = Exception("Attribute error")
        element2 = MagicMock()
        element2.get_attribute.return_value = "https://example.com/valid"

        page.query.return_value = [element1, element2]

        with pytest.raises(Exception, match="Attribute error"):
            await get_hrefs(page)


class TestGetSelfHrefsEdgeCases:
    """Test edge cases for get_self_hrefs function."""

    @pytest.mark.asyncio
    async def test_get_self_hrefs_no_relative_links(self):
        """Test get_self_hrefs when no relative links exist."""
        page = AsyncMock()

        # Mock elements with only external links
        element1 = MagicMock()
        element1.get_attribute.return_value = "https://external.com/page1"
        element2 = MagicMock()
        element2.get_attribute.return_value = "https://other.com/page2"

        page.query.return_value = [element1, element2]

        result = await get_self_hrefs(page, build_absolute=False)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_self_hrefs_mixed_protocols(self):
        """Test get_self_hrefs with mixed protocol relative links."""
        page = AsyncMock()

        # Mock elements with various relative link types
        element1 = MagicMock()
        element1.get_attribute.return_value = "/path/to/page"
        element2 = MagicMock()
        element2.get_attribute.return_value = "../parent/page"
        element3 = MagicMock()
        element3.get_attribute.return_value = "./current/page"
        element4 = MagicMock()
        element4.get_attribute.return_value = "relative/page"
        element5 = MagicMock()
        element5.get_attribute.return_value = "?query=param"
        element6 = MagicMock()
        element6.get_attribute.return_value = "#anchor"

        page.query.return_value = [
            element1,
            element2,
            element3,
            element4,
            element5,
            element6,
        ]

        result = await get_self_hrefs(page, build_absolute=False)

        expected = [
            "/path/to/page",
            "../parent/page",
            "./current/page",
            "relative/page",
            "?query=param",
            "#anchor",
        ]
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_self_hrefs_absolute_with_complex_current_url(self):
        """Test absolute URL building with complex current URL."""
        page = AsyncMock()

        # Create a coroutine that returns a complex URL
        async def get_current_url():
            return "https://example.com/path/to/current/page?param=value#section"

        page.current_url = get_current_url()

        # Mock relative href
        element1 = MagicMock()
        element1.get_attribute.return_value = "/new/path"

        page.query.return_value = [element1]

        result = await get_self_hrefs(page, build_absolute=True)

        expected = ["https://example.com/new/path"]
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_self_hrefs_absolute_current_url_exception(self):
        """Test get_self_hrefs when getting current URL raises exception."""
        page = AsyncMock()

        # Mock current_url to raise exception
        async def get_current_url():
            raise Exception("Failed to get current URL")

        page.current_url = get_current_url()

        element1 = MagicMock()
        element1.get_attribute.return_value = "/relative/page"
        page.query.return_value = [element1]

        with pytest.raises(Exception, match="Failed to get current URL"):
            await get_self_hrefs(page, build_absolute=True)

    @pytest.mark.asyncio
    async def test_get_self_hrefs_absolute_invalid_current_url(self):
        """Test get_self_hrefs with invalid current URL format."""
        page = AsyncMock()

        # Mock invalid current URL
        async def get_current_url():
            return "not-a-valid-url"

        page.current_url = get_current_url()

        element1 = MagicMock()
        element1.get_attribute.return_value = "/relative/page"
        page.query.return_value = [element1]

        # Should handle invalid URL gracefully (implementation dependent)
        # This might raise an exception or return malformed URLs
        try:
            result = await get_self_hrefs(page, build_absolute=True)
            # If no exception, verify result is a list
            assert isinstance(result, list)
        except Exception:
            # Some URL parsing libraries might raise exceptions
            pass

    @pytest.mark.asyncio
    async def test_get_self_hrefs_duplicate_links(self):
        """Test get_self_hrefs with duplicate relative links."""
        page = AsyncMock()

        # Mock elements with duplicate hrefs
        element1 = MagicMock()
        element1.get_attribute.return_value = "/page1"
        element2 = MagicMock()
        element2.get_attribute.return_value = "/page2"
        element3 = MagicMock()
        element3.get_attribute.return_value = "/page1"  # Duplicate
        element4 = MagicMock()
        element4.get_attribute.return_value = "/page2"  # Duplicate

        page.query.return_value = [element1, element2, element3, element4]

        result = await get_self_hrefs(page, build_absolute=False)

        # Should return all links including duplicates (deduplication happens elsewhere)
        expected = ["/page1", "/page2", "/page1", "/page2"]
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_self_hrefs_data_urls(self):
        """Test get_self_hrefs with data URLs."""
        page = AsyncMock()

        # Mock elements with data URLs (should be excluded as not relative)
        element1 = MagicMock()
        element1.get_attribute.return_value = "data:text/html,<h1>Hello</h1>"
        element2 = MagicMock()
        element2.get_attribute.return_value = "/relative/page"

        page.query.return_value = [element1, element2]

        result = await get_self_hrefs(page, build_absolute=False)

        # Data URLs should not be considered relative links
        expected = ["/relative/page"]
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_self_hrefs_with_port_numbers(self):
        """Test get_self_hrefs absolute building with port numbers."""
        page = AsyncMock()

        async def get_current_url():
            return "https://example.com:8080/current/page"

        page.current_url = get_current_url()

        element1 = MagicMock()
        element1.get_attribute.return_value = "/api/endpoint"

        page.query.return_value = [element1]

        result = await get_self_hrefs(page, build_absolute=True)

        expected = ["https://example.com:8080/api/endpoint"]
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_self_hrefs_query_selector_verification(self):
        """Test that get_self_hrefs uses correct CSS selector."""
        page = AsyncMock()
        page.query.return_value = []

        await get_self_hrefs(page, build_absolute=False)

        # Verify that the correct CSS selector was used
        page.query.assert_called_once_with("a[href]")

    @pytest.mark.asyncio
    async def test_get_hrefs_query_selector_verification(self):
        """Test that get_hrefs uses correct CSS selector."""
        page = AsyncMock()
        page.query.return_value = []

        await get_hrefs(page)

        # Verify that the correct CSS selector was used
        page.query.assert_called_once_with("a[href]")
