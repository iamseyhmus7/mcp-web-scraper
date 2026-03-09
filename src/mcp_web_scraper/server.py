import asyncio
import uuid
import datetime
from typing import Dict, Any, List
import pydantic
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
import mcp.types as types

from mcp_web_scraper.browser import browser_pool
from mcp_web_scraper.scraper import (
    scrape_page as scrape_action,
    extract_table as table_action,
    get_links as links_action,
    fill_form as form_action,
    take_screenshot_action,
    watch_page as watch_action
)
from mcp_web_scraper.queue import job_queue
import anyio

server = Server("mcp-web-scraper")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="scrape_page",
            description="Sayfadan icerik, baslik ve metadata cikarir.",
            inputSchema={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"]
            }
        ),
        types.Tool(
            name="extract_table",
            description="HTML tabloyu JSON array'e cevirir (sayfadaki ilk tabloyu baz alir).",
            inputSchema={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"]
            }
        ),
        types.Tool(
            name="get_links",
            description="Sayfadaki tum linkleri filtreli olarak listeler.",
            inputSchema={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"]
            }
        ),
        types.Tool(
            name="fill_form",
            description="CSS selector ile form doldur ve gonder.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "fields": {"type": "object", "additionalProperties": {"type": "string"}}
                },
                "required": ["url", "fields"]
            }
        ),
        types.Tool(
            name="take_screenshot",
            description="Tam sayfa ekran goruntusu al, base64 dondur.",
            inputSchema={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"]
            }
        ),
        types.Tool(
            name="scrape_queue",
            description="Coklu URL'leri kuyruga ekle, job_id dondur.",
            inputSchema={
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["urls"]
            }
        ),
        types.Tool(
            name="watch_page",
            description="Sayfa degisikligini periyodik izle ve degisiklik olunca dondur (Polling). İlk degisiklikte cikar.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "interval_seconds": {"type": "integer"},
                    "max_checks": {"type": "integer", "default": 60}
                },
                "required": ["url", "interval_seconds"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if not arguments:
        arguments = {}

    import json

    if name == "scrape_page":
        res = await scrape_action(arguments["url"])
        return [types.TextContent(type="text", text=json.dumps(res, ensure_ascii=False))]
        
    elif name == "extract_table":
        res = await table_action(arguments["url"])
        return [types.TextContent(type="text", text=json.dumps(res, ensure_ascii=False))]
        
    elif name == "get_links":
        res = await links_action(arguments["url"])
        return [types.TextContent(type="text", text=json.dumps(res, ensure_ascii=False))]
        
    elif name == "fill_form":
        res = await form_action(arguments["url"], arguments["fields"])
        return [types.TextContent(type="text", text=json.dumps(res, ensure_ascii=False))]
        
    elif name == "take_screenshot":
        job_id = str(uuid.uuid4())
        b64 = await take_screenshot_action(arguments["url"], job_id)
        return [types.TextContent(type="text", text=json.dumps({"job_id": job_id, "screenshot_base64": b64}))]
        
    elif name == "scrape_queue":
        job_id = await job_queue.enqueue_jobs(arguments["urls"])
        return [types.TextContent(type="text", text=json.dumps({"job_id": job_id, "status": "queued"}))]
        
    elif name == "watch_page":
        import hashlib
        max_checks = arguments.get("max_checks", 60)
        url = arguments["url"]
        interval = arguments["interval_seconds"]
        
        async for event in watch_action(url, interval):
            if event["event"] == "page_changed" or event.get("error"):
                return [types.TextContent(type="text", text=json.dumps(event, ensure_ascii=False))]
            # the watch_started yields, but we want to continue checking until max checks
            max_checks -= 1
            if max_checks <= 0:
                break
        return [types.TextContent(type="text", text=json.dumps({"event": "timeout", "url": url}))]

    raise ValueError(f"Unknown tool: {name}")

async def main_async():
    # Initialize Browser Pool properly
    await browser_pool.get_browser()
    
    # Initialize Stream manually since anyio.create_memory_object_stream must be in the active loop
    job_queue.send_stream, job_queue.receive_stream = anyio.create_memory_object_stream(100)
    
    # Start background workers
    workers = []
    for _ in range(job_queue.max_workers):
        workers.append(asyncio.create_task(job_queue._worker()))
        job_queue._workers_started = True

    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mcp-web-scraper",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    finally:
        for w in workers:
            w.cancel()
        await browser_pool.close()

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
