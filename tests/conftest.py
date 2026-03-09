import pytest
from unittest.mock import AsyncMock
from contextlib import asynccontextmanager

@pytest.fixture
def mock_page():
    page = AsyncMock()
    page.content.return_value = "<html><head><meta name='description' content='test desc'></head><body><table><tr><td>col1</td><td>col2</td></tr></table><a href='http://test.com'>link</a></body></html>"
    page.title.return_value = "Test Page"
    page.screenshot.return_value = b"fake_image_data"
    
    # Simulate page.goto with potential timeout exceptions
    async def mock_goto(url, **kwargs):
        if "timeout" in url:
            from playwright.async_api import TimeoutError as PlwTimeoutError
            raise PlwTimeoutError("Timeout exceeded")
        if "invalid" in url:
            raise Exception("Invalid URL")
        return None
        
    page.goto.side_effect = mock_goto
    return page

@pytest.fixture(autouse=True)
def mock_browser_pool(mocker, mock_page):
    @asynccontextmanager
    async def mock_acquire():
        yield mock_page
        
    # Patch the global browser_pool's acquire method used by scraper
    mocker.patch("mcp_web_scraper.browser.browser_pool.acquire", side_effect=mock_acquire)
