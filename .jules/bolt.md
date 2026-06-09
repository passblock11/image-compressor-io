## 2025-05-22 - [Pillow to pyvips Migration]
**Learning:** Migrating from Pillow to pyvips for JPEG compression and resizing provided a ~67% reduction in latency (from ~0.3s to ~0.1s for a 3000x3000px image). Using `thumbnail_buffer` is critical for high-performance resizing as it performs shrink-on-load.
**Action:** Always prefer `pyvips` for CPU-intensive image processing tasks in high-throughput APIs. Ensure `libvips-dev` is present in the environment.

## 2025-05-22 - [FastAPI Synchronous Endpoints for CPU-bound tasks]
**Learning:** For CPU-bound tasks like image compression, using synchronous `def` endpoints in FastAPI is more efficient than `async def` because it offloads the work to a thread pool, preventing the event loop from being blocked.
**Action:** Use synchronous `def` for CPU-intensive operations in FastAPI to improve concurrency and responsiveness.
