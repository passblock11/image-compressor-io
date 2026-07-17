## 2025-02-18 - Migrating to pyvips with thread pool delegation in FastAPI
**Learning:** Migrating image processing from Pillow to pyvips and switching from `async def` to synchronous `def` avoids blocking FastAPI's event loop with CPU-bound work. In addition, using pyvips's `thumbnail_buffer` enables "shrink-on-load" which significantly improves performance compared to Pillow's resize.
**Action:** Always prefer synchronous `def` endpoints for CPU-bound tasks in FastAPI, and use `pyvips` with `new_from_buffer` and `thumbnail_buffer` for high-performance image manipulation.
