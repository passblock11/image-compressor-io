## 2025-05-14 - FastAPI Sync vs Async for CPU-bound tasks

**Learning:** Using `async def` for endpoints that perform heavy CPU-bound work (like image processing) blocks the main event loop, preventing the server from handling other requests. FastAPI handles synchronous `def` endpoints by running them in a separate thread pool.

**Action:** Always use synchronous `def` for image processing endpoints in FastAPI to maintain high concurrency and prevent event loop starvation.

## 2025-05-14 - Pyvips Thumbnail Optimization

**Learning:** `pyvips.Image.thumbnail_buffer` is significantly faster than loading a full image and kemudian resizing because it performs shrinking during the load process (at the libjpeg level if applicable).

**Action:** Prefer `thumbnail_buffer` or `thumbnail_image` over separate load and resize operations when the target dimensions are known.
