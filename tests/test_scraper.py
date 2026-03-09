import pytest
import asyncio
from playwright.async_api import TimeoutError as PlwTimeoutError

from mcp_web_scraper.scraper import (
    scrape_page,
    extract_table,
    get_links,
    fill_form,
    take_screenshot_action,
    watch_page
)

@pytest.mark.asyncio
async def test_scrape_page_success():
    res = await scrape_page("http://example.com")
    assert res["title"] == "Test Page"
    assert "col1" in res["content"]
    assert res["metadata"]["description"] == "test desc"

@pytest.mark.asyncio
async def test_scrape_page_timeout():
    with pytest.raises(Exception):
        # We also configured tenacity retry on the scraper functions. 
        # So tenacity will retry 3 times then raise the Exception.
        await scrape_page("http://timeout.com")

@pytest.mark.asyncio
async def test_scrape_page_invalid():
    with pytest.raises(Exception):
        await scrape_page("http://invalid.com")

@pytest.mark.asyncio
async def test_extract_table_success():
    res = await extract_table("http://example.com")
    assert len(res) == 1
    assert res[0] == ["col1", "col2"]

@pytest.mark.asyncio
async def test_get_links_success():
    res = await get_links("http://example.com")
    assert len(res) == 1
    assert res[0]["text"] == "link"
    assert res[0]["href"] == "http://test.com"

@pytest.mark.asyncio
async def test_fill_form_success(mock_page):
    res = await fill_form("http://example.com", {"input[name='user']": "admin"})
    assert res["title"] == "Test Page"
    mock_page.fill.assert_called_with("input[name='user']", "admin")

@pytest.mark.asyncio
async def test_take_screenshot(mocker):
    # Mock storage so we don't write to disk
    mocker.patch("mcp_web_scraper.scraper.save_screenshot", return_value="/tmp/test.png")
    mocker.patch("mcp_web_scraper.scraper.get_base64_screenshot", return_value="base64str")
    
    res = await take_screenshot_action("http://example.com", "job-123")
    assert res == "base64str"

@pytest.mark.asyncio
async def test_watch_page(mock_page):
    gen = watch_page("http://example.com", interval_seconds=0.1)
    
    mock_page.content.return_value = "<html><body>First</body></html>"
    
    # First yield should be watching_started
    event1 = await anext(gen)
    assert event1["event"] == "watching_started"
    
    # Now change content to trigger page_changed
    mock_page.content.return_value = "<html><body>Second</body></html>"
    
    # Second yield should be page_changed
    event2 = await anext(gen)
    assert event2["event"] == "page_changed"
    assert event2["url"] == "http://example.com"
