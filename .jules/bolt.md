## 2025-05-15 - [Pillow to pyvips Migration & Sync Endpoint]
**Learning:** Migrating from Pillow to pyvips and switching from `async def` to synchronous `def` significantly improves performance for CPU-bound image processing. pyvips's 'shrink-on-load' (via `thumbnail_buffer`) avoids decoding full images, reducing both latency and memory usage.
**Action:** Always prefer pyvips for high-performance image processing and use synchronous endpoints in FastAPI for CPU-bound tasks to leverage the external thread pool and prevent event loop blockage.
