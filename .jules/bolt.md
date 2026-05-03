## 2026-05-03 - [Vips vs Pillow Performance]
**Learning:** pyvips is significantly faster than Pillow for image resizing and compression, especially when using `thumbnail_buffer` which performs shrink-on-load. Migrating a FastAPI endpoint from `async def` to `def` for CPU-bound image processing avoids event loop blocking and leverages the thread pool effectively.
**Action:** Use pyvips for high-performance image processing tasks. Always ensure system dependencies (`libvips-dev`) are available. Use synchronous endpoints in FastAPI for CPU-intensive work.
