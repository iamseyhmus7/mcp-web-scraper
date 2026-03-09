import asyncio
import hashlib
from typing import Dict, Any, List, AsyncGenerator
from bs4 import BeautifulSoup
from tenacity import retry, wait_fixed, stop_after_attempt

from mcp_web_scraper.browser import browser_pool
from mcp_web_scraper.storage import save_screenshot, get_base64_screenshot

@retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
async def scrape_page(url: str) -> Dict[str, Any]:
    async with browser_pool.acquire() as page:
        await page.goto(url, timeout=30000, wait_until="networkidle")
        content = await page.content()
        title = await page.title()
        
        soup = BeautifulSoup(content, "lxml")
        
        metadata = {}
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content_val = meta.get("content")
            if name and content_val:
                metadata[name] = content_val

        return {
            "url": url,
            "title": title,
            "content": soup.get_text(separator="\n", strip=True),
            "metadata": metadata
        }

@retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
async def extract_table(url: str) -> List[List[str]]:
    async with browser_pool.acquire() as page:
        await page.goto(url, timeout=30000, wait_until="networkidle")
        await page.wait_for_selector("table", timeout=10000)
        content = await page.content()
        
        soup = BeautifulSoup(content, "lxml")
        table = soup.find("table")
        if not table:
            return []
            
        result = []
        for row in table.find_all("tr"):
            cols = row.find_all(["td", "th"])
            result.append([col.get_text(strip=True) for col in cols])
            
        return result

@retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
async def get_links(url: str) -> List[Dict[str, str]]:
    async with browser_pool.acquire() as page:
        await page.goto(url, timeout=30000, wait_until="networkidle")
        content = await page.content()
        
        soup = BeautifulSoup(content, "lxml")
        links = []
        for a in soup.find_all("a", href=True):
            links.append({
                "text": a.get_text(strip=True),
                "href": a["href"]
            })
        return links

@retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
async def fill_form(url: str, fields: Dict[str, str]) -> Dict[str, Any]:
    async with browser_pool.acquire() as page:
        await page.goto(url, timeout=30000, wait_until="networkidle")
        
        for selector, value in fields.items():
            await page.fill(selector, value)
            
        # Try to find a submit button and click it
        submit_button = await page.query_selector("button[type='submit'], input[type='submit']")
        if submit_button:
            await submit_button.click()
            await page.wait_for_load_state("networkidle", timeout=30000)
            
        content = await page.content()
        soup = BeautifulSoup(content, "lxml")
        return {
            "url": url,
            "title": await page.title(),
            "content_snippet": soup.get_text(separator="\n", strip=True)[:500]
        }

@retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
async def take_screenshot_action(url: str, job_id: str) -> str:
    async with browser_pool.acquire() as page:
        await page.goto(url, timeout=30000, wait_until="networkidle")
        screenshot_bytes = await page.screenshot(full_page=True)
        path = save_screenshot(job_id, screenshot_bytes)
        return get_base64_screenshot(path)

async def watch_page(url: str, interval_seconds: int) -> AsyncGenerator[Dict[str, str], None]:
    last_hash = None
    
    while True:
        try:
            async with browser_pool.acquire() as page:
                await page.goto(url, timeout=30000, wait_until="networkidle")
                content = await page.content()
                
            current_hash = hashlib.md5(content.encode()).hexdigest()
            
            # According to User rules, use hashlib Polling for watch_page
            if last_hash is not None and current_hash != last_hash:
                yield {
                    "url": url,
                    "event": "page_changed",
                    "hash": current_hash
                }
            elif last_hash is None:
                # Still yield a "started" event to not block arbitrarily
                last_hash = current_hash
                yield {
                    "url": url,
                    "event": "watching_started",
                    "hash": current_hash
                }
                
            last_hash = current_hash
            await asyncio.sleep(interval_seconds)
        except Exception as e:
            yield {
                "url": url,
                "event": "error",
                "error": str(e)
            }
            raise e
