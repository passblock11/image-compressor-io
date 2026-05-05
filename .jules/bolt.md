## 2025-05-15 - [FastAPI CPU-bound tasks]
**Learning:** For CPU-bound tasks like image processing, using `def` instead of `async def` in FastAPI is faster because it automatically uses a threadpool, preventing the event loop from being blocked by heavy computations.
**Action:** Always use synchronous `def` for image processing endpoints in FastAPI.

## 2025-05-15 - [Pyvips performance advantage]
**Learning:** `pyvips` with `thumbnail_buffer` is significantly faster than Pillow for resizing because it performs the operation during loading and uses libvips' efficient pipeline.
**Action:** Prefer `pyvips` for high-performance image resizing and compression tasks.
