## 2025-05-22 - libvips migration for image compression
**Learning:** Migrating from Pillow to libvips (pyvips) and switching from async to sync endpoints in FastAPI can reduce image compression latency by ~70%. Using `thumbnail_buffer` allows for efficient resizing during the load phase.
**Action:** Always prefer pyvips for high-performance image processing if available. Use synchronous `def` for CPU-bound tasks in FastAPI to leverage the external thread pool.

## 2025-05-22 - FastAPI Error Handling Anti-pattern
**Learning:** Broad `except Exception` blocks in FastAPI endpoints can swallow specific `HTTPException` instances, leading to incorrect 400 status codes instead of the intended specific errors (e.g., 413 File Too Large).
**Action:** Always catch and re-raise `HTTPException` before a general `except` block or use more specific exception handling.
