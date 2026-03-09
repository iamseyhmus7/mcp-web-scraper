# Python Style Guide
- Force `async`/`await` for all synchronous-looking API calls to IO operations.
- Avoid global mutable dependencies inside tool handlers without cross-thread/async-task synchronization. Use `asyncio.Lock()`.
- Run tests regularly using `pytest`. Follow `.py` standards.
