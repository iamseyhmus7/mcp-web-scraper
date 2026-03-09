# Playwright Rules
- **DO NOT** launch new browser objects for every request. Always use the `BrowserPool.acquire()` logic.
- Ensure `stealth_async` is used consistently against pages to evade Anti-Bot detection.
- Must execute `await page.goto(url, wait_until="networkidle", timeout=30000)`. Wait timeouts are strictly required.
