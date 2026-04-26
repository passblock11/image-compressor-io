## 2025-05-14 - Performance improvement with pyvips

**Learning:** Migrating from Pillow to pyvips significantly reduces latency for image processing tasks. Specifically, using `thumbnail_buffer` allows for extremely fast resizing during the loading process, avoiding full image decoding of high-resolution images. Switching from `async def` to `def` in FastAPI for CPU-bound tasks like image processing allows them to run in a thread pool, preventing blocking of the event loop.

**Action:** Use `pyvips` for image-heavy APIs. Always use `thumbnail_buffer` for resizing if possible. Prefer synchronous endpoints (`def`) for CPU-bound processing in FastAPI to leverage its built-in thread pool.
