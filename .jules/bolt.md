## 2025-05-15 - [Synchronous CPU-bound Endpoints in FastAPI]
**Learning:** In FastAPI, using `async def` for CPU-bound tasks (like image processing) blocks the event loop, preventing the server from handling other requests concurrently. Switching to a standard `def` allows FastAPI to delegate the work to an external thread pool.
**Action:** Always use synchronous `def` for CPU-intensive image processing tasks in FastAPI.

## 2025-05-15 - [pyvips vs Pillow for Image Compression]
**Learning:** Migrating from Pillow to pyvips with `thumbnail_buffer` resulted in a ~64% reduction in latency (0.31s to 0.11s) for 3000x3000px JPEG images.
**Action:** Prioritize `pyvips` with `thumbnail_buffer` for high-performance image resizing and compression.
