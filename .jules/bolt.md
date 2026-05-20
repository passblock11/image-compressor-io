## 2025-05-20 - [Pyvips Migration & Sync Endpoint]
**Learning:** Migrating from Pillow to pyvips with synchronous endpoints and `thumbnail_buffer` achieved a ~65% latency reduction (from ~0.30s to ~0.10s) for 3000x3000px images in the `/compress` endpoint. Using `thumbnail_buffer` is significantly faster as it performs shrinking during load. Switching from `async def` to `def` for CPU-bound tasks in FastAPI avoids blocking the event loop and leverages a thread pool.
**Action:** Prefer pyvips for heavy image processing and use synchronous endpoints in FastAPI for CPU-intensive operations.
