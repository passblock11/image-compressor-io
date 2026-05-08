## 2025-05-15 - Migrating to pyvips and synchronous FastAPI endpoints

**Learning:** For CPU-bound tasks like image processing, FastAPI's synchronous `def` endpoints are more efficient than `async def` as they run in a thread pool and don't block the event loop. Additionally, `pyvips.Image.thumbnail_buffer` provides a massive performance boost over Pillow by performing the resize operation during the image loading phase.

**Action:** Use synchronous endpoints for image processing and prioritize `pyvips` with `thumbnail_buffer` for high-performance resizing.
