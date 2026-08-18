# Bolt Journal

## 2025-05-20 - Fast C-level Image Processing with pyvips in FastAPI
**Learning:** `pyvips` leverages libvips's C-level pipeline and shrink-on-load capability (`pyvips.Image.thumbnail_buffer`), delivering up to 4.14x speedup (~75.9% reduction in latency) compared to Pillow's `resize(Image.LANCZOS)`. In FastAPI, converting CPU-bound endpoint functions from `async def` to synchronous `def` allows FastAPI to execute the image processing on threadpool workers, preventing event loop contention.
**Action:** Always prefer `pyvips` with shrink-on-load for image compression microservices where `pyvips` is present in requirements and `libvips` is configured, and route heavy CPU tasks to worker threads via synchronous `def` handlers in FastAPI.
