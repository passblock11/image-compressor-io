## 2025-06-25 - [Migrating to pyvips and sync endpoint]
**Learning:** Migrating from Pillow to pyvips for image processing provides significant performance gains, especially when using "shrink-on-load" (thumbnail_buffer). Furthermore, switching CPU-bound FastAPI endpoints from `async def` to `def` prevents blocking the event loop and leverages FastAPI's external thread pool, improving concurrent throughput.
**Action:** Always consider pyvips for performance-critical image processing and prefer sync `def` for CPU-bound tasks in FastAPI.
