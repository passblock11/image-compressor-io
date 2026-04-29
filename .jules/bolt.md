## 2025-05-15 - Migrating from Pillow to pyvips for Image Compression

**Learning:** Transitioning from Pillow to `pyvips` with `thumbnail_buffer` and using synchronous FastAPI endpoints resulted in a ~65% latency reduction (from ~0.29s to ~0.10s) for 3000x3000px JPEG images. `pyvips` is significantly more efficient for large image operations due to its "shrink-on-load" capability and lower memory overhead. Additionally, for CPU-bound tasks like image processing, synchronous endpoints are preferred in FastAPI as they are automatically offloaded to a thread pool, preventing the event loop from being blocked.

**Action:** Prefer `pyvips` over Pillow for high-performance image processing tasks. Always use `thumbnail_buffer` when resizing during the load phase. Use synchronous `def` instead of `async def` for CPU-intensive endpoints in FastAPI.
