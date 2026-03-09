# mcp-web-scraper

Autonomous web scraper exposed via the **Model Context Protocol (MCP)** using **Playwright**.

## Features
- **scrape_page**: Extract contents, title, and metadata from any Javascript-rendered URL.
- **scrape_queue**: Queue multiple URLs for background processing efficiently.
- **watch_page**: Monitor pages periodically for hashing changes.
- **take_screenshot**: Return base64-encoded full-page screenshots.
- **fill_form**: Fill HTML forms via CSS selectors and submit them safely.
- **extract_table**: Extract structural JSON array representations of tables on the page.
- **get_links**: Enumerate all available links.

## Requirements
- Python >= 3.10
- Chromium browsers installed via `playwright install chromium`

## Local Execution
You can use `uv` or `pip` to install from source.

```bash
pip install .
python -m mcp_web_scraper
```

### Dev server
```bash
mcp dev src/mcp_web_scraper/server.py
```
