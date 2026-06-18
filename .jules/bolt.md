## 2025-05-15 - [pyvips Migration for Image Compression]
**Learning:** Migrating from Pillow to pyvips for image resizing and JPEG encoding significantly reduces latency for large images. Specifically, `pyvips.Image.thumbnail_buffer` is much faster than Pillow's `Image.resize` because it leverages "shrink-on-load" optimizations. Additionally, switching the FastAPI endpoint from `async def` to synchronous `def` for CPU-bound tasks improves throughput by offloading work to a thread pool, preventing event loop blockage.

**Action:** Prefer `pyvips` for high-performance image processing pipelines and use synchronous `def` in FastAPI for heavy CPU-bound operations.
