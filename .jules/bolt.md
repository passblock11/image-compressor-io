## 2026-03-31 - Leveraging pyvips & Sync Endpoints for Image Resizing in FastAPI

**Learning:** `pyvips` provides significant performance improvements (~64% latency reduction) over Pillow (`PIL.Image`) for image resizing and JPEG compression because `pyvips` streams and processes image pixels on-demand. Making the endpoint synchronous (`def`) allows FastAPI to execute the CPU-heavy image processing tasks in its external thread pool without blocking the main asyncio event loop.
**Action:** Use `pyvips` with synchronous `def` endpoints for CPU-bound image compression tasks when `pyvips` and `libvips` are available.
