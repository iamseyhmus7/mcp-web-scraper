import asyncio
import json

from mcp_web_scraper.scraper import scrape_page, extract_table, get_links, take_screenshot_action, fill_form, watch_page
from mcp_web_scraper.browser import browser_pool

async def main():
    await browser_pool.get_browser()
    try:
        url = "https://www.e-ticaretarkadasim.com/"
        print(f"--- Testing scrape_page on {url} ---")
        page_data = await scrape_page(url)
        print(f"Title: {page_data['title']}")
        print(f"Content length: {len(page_data['content'])} chars")
        print(f"Content snippet: {page_data['content'][:100]}...\n")

        print(f"--- Testing get_links on {url} ---")
        links = await get_links(url)
        print(f"Found {len(links)} links.")
        if links:
            print(f"First link: {links[0]}\n")
            
        print(f"--- Testing take_screenshot on {url} ---")
        b64_img = await take_screenshot_action(url, "test-job-123")
        print(f"Screenshot taken, base64 length: {len(b64_img)} chars.\n")
        
        wiki_url = "https://en.wikipedia.org/wiki/Web_scraping"
        print(f"--- Testing extract_table on {wiki_url} ---")
        table_data = await extract_table(wiki_url)
        print(f"Found table with {len(table_data)} rows.")
        if table_data:
            print(f"First row: {table_data[0]}")
            
        print("\n--- Testing fill_form on https://www.e-ticaretarkadasim.com/ ---")
        try:
            # We just test the selector without actually expecting it to submit correctly on example.com since there is no form
            form_res = await fill_form("https://www.e-ticaretarkadasim.com/", {"body": "test"})
            print(f"Form fill returned: title={form_res['title']}, url={form_res['url']}\n")
        except Exception as e:
            print(f"Form fill expectedly threw an error on example.com: {e}\n")

        print("--- Testing watch_page on https://www.e-ticaretarkadasim.com/ ---")
        async for event in watch_page("https://www.e-ticaretarkadasim.com/", interval_seconds=1):
            print(f"Watch page event: {event}")
            break # Just get the first event and break out of the generator
        
        print("\n--- Testing scrape_queue ---")
        from mcp_web_scraper.queue import job_queue
        from mcp_web_scraper.storage import jobs
        # ensure workers are running since we bypass the server lifespan
        import anyio
        job_queue.send_stream, job_queue.receive_stream = anyio.create_memory_object_stream(10)
        task = asyncio.create_task(job_queue._worker())
        
        q_job_id = await job_queue.enqueue_jobs(["https://www.e-ticaretarkadasim.com/"])
        print(f"Enqueued job: {q_job_id}")
        
        # We loop and wait until status is completed (up to 30 seconds)
        for _ in range(30):
            job_status = jobs.get(q_job_id)
            if job_status and job_status['status'] == 'completed':
                print(f"Job Status: {job_status['status']}, Completed: {job_status['completed']}")
                break
            await asyncio.sleep(1)
        else:
            job_status = jobs.get(q_job_id)
            print(f"Job Status: {job_status['status'] if job_status else 'Unknown'} (Timeout after 30s)")
                
        task.cancel()
            
    finally:
        await browser_pool.close()

if __name__ == "__main__":
    asyncio.run(main())
