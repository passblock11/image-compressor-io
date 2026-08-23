## 2026-03-31 - Fast Image Processing with pyvips and Starlette Worker Threads
**Learning:**
1. Using `pyvips.Image.thumbnail_image` on an opened lazy Image buffer provides shrink-on-load optimization while preserving pre-applied color space and alpha flattening transformations without re-reading the byte array.
2. Converting CPU-bound FastAPI routes from `async def` to `def` prevents blocking the main asyncio event loop by delegating image processing execution to Starlette's worker thread pool.

**Action:**
1. Always use `def` for heavy CPU-bound image encoding/decoding tasks in FastAPI endpoints.
2. Leverage `pyvips` lazy loading and C-level operations for high-throughput image processing workloads.
