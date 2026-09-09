## 2026-03-09 - High-Performance Image Compression with PyVips & Sync FastAPI Endpoints
**Learning:** For CPU-bound image processing tasks in FastAPI, changing `async def` to synchronous `def` offloads work from the main asyncio event loop to Starlette's thread pool. Additionally, replacing Pillow with `pyvips` leverages libvips fast SIMD C-library operations, reducing processing latency by ~54%.
**Action:** When handling heavy image manipulation endpoints, prefer synchronous `def` endpoints and `pyvips` buffer methods (`new_from_buffer`, `thumbnail_image`, `jpegsave_buffer`).
