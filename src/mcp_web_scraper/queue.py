import uuid
import datetime
import anyio
from typing import List, Dict, Any

from mcp_web_scraper.storage import jobs
from mcp_web_scraper.scraper import scrape_page

class JobQueue:
    def __init__(self, max_workers=3):
        self.max_workers = max_workers
        self.send_stream = None
        self.receive_stream = None
        self._workers_started = False

    async def _worker(self):
        if not self.receive_stream:
            return
        async with self.receive_stream:
            async for job_data in self.receive_stream:
                job_id = job_data["job_id"]
                url = job_data["url"]
                
                job = jobs.get(job_id)
                if not job:
                    continue
                    
                if job["status"] == "pending":
                    job["status"] = "running"
                    job["updated_at"] = datetime.datetime.now(datetime.UTC).isoformat()

                try:
                    result = await scrape_page(url)
                    job["results"].append({"url": url, "success": True, "data": result})
                    job["completed"] += 1
                except Exception as e:
                    job["results"].append({"url": url, "success": False, "error": str(e)})
                    job["failed"] += 1
                    
                job["updated_at"] = datetime.datetime.now(datetime.UTC).isoformat()
                
                # Check if job is completed
                if job["completed"] + job["failed"] == job["total"]:
                    job["status"] = "completed" if job["failed"] == 0 else "failed"

    async def start_workers(self, task_group: anyio.abc.TaskGroup):
        if not self._workers_started:
            if not self.send_stream:
                self.send_stream, self.receive_stream = anyio.create_memory_object_stream(100)
            for _ in range(self.max_workers):
                task_group.start_soon(self._worker)
            self._workers_started = True

    async def enqueue_jobs(self, urls: List[str]) -> str:
        if not self.send_stream:
            self.send_stream, self.receive_stream = anyio.create_memory_object_stream(100)
            
        # Active job logic checks could be added here
        
        job_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.UTC).isoformat()
        
        jobs[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "total": len(urls),
            "completed": 0,
            "failed": 0,
            "results": [],
            "created_at": now,
            "updated_at": now
        }
        
        for url in urls:
            await self.send_stream.send({"job_id": job_id, "url": url})
            
        return job_id

# Global queue singleton
job_queue = JobQueue(max_workers=3)
