## 2025-05-15 - [Pyvips Migration and Sync Endpoint]
**Learning:** Migrating from Pillow to pyvips and switching to a synchronous `def` endpoint in FastAPI significantly improves performance for CPU-bound image processing tasks by leveraging libvips' speed and FastAPI's internal thread pool. The use of `thumbnail_buffer` in pyvips provides further gains via "shrink-on-load" optimization.
**Action:** Use pyvips and `def` endpoints for heavy image processing tasks in the future.
