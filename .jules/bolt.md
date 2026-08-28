## 2026-08-28 - Pyvips Migration & Synchronous FastAPI Endpoints for Image Processing

**Learning:** Replacing Pillow with `pyvips` leverages libvips' C-level shrink-on-load capability (`pyvips.Image.thumbnail_buffer`), avoiding loading full-resolution uncompressed image arrays into Python memory during resize operations. Furthermore, defining CPU-bound FastAPI endpoints as synchronous `def` (instead of `async def`) offloads image processing to Starlette's worker thread pool, preventing CPU execution from blocking FastAPI's main asyncio event loop.

**Action:** For CPU-intensive image or file processing in FastAPI microservices, use high-performance C-backed libraries like `pyvips` with shrink-on-load and declare endpoints synchronously to utilize thread pool concurrency.
