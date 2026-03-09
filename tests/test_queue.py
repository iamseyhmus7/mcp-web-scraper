import pytest
import anyio
import asyncio

from mcp_web_scraper.queue import JobQueue
from mcp_web_scraper.storage import jobs

@pytest.mark.asyncio
async def test_queue_processing_success_and_failure(mocker):
    # Mock scrape_page so we don't need real browsing, just test the queue logic
    async def mock_scrape(url):
        if "invalid" in url:
            raise Exception("Failure")
        return {"result": f"Scraped {url}"}

    mocker.patch("mcp_web_scraper.queue.scrape_page", side_effect=mock_scrape)

    q = JobQueue(max_workers=3)
    
    # Initialize streams inside the current active loop
    q.send_stream, q.receive_stream = anyio.create_memory_object_stream(100)

    # We need 3 URLs -> 2 success + 1 failure
    urls = [
        "http://example1.com",
        "http://example2.com",
        "http://invalid.com"
    ]

    # Enqueue logic (borrowed from JobQueue manually for testing, or using the actual enqueue_jobs)
    # Actually, we should test the q.enqueue_jobs method itself
    
    async def run_queue_test():
        job_id = await q.enqueue_jobs(urls)
        assert job_id in jobs
        
        async with anyio.create_task_group() as tg:
            await q.start_workers(tg)
            
            # Wait for job to process
            for _ in range(20):
                if jobs[job_id]["status"] in ["completed", "failed"]:
                    break
                await asyncio.sleep(0.1)
                
            # Stop workers
            tg.cancel_scope.cancel()
            
        return job_id

    job_id = await run_queue_test()
    job = jobs[job_id]
    
    assert job["total"] == 3
    assert job["completed"] == 2
    assert job["failed"] == 1
    assert job["status"] == "failed" # since one failed
    
    success_urls = [r["url"] for r in job["results"] if r.get("success")]
    assert "http://example1.com" in success_urls
    assert "http://invalid.com" not in success_urls
