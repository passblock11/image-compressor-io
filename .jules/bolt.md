## 2025-02-18 - Fast Image Downscaling with pyvips & FastAPI Threadpool
**Learning:** For CPU-bound image processing in FastAPI, running tasks synchronously (`def` endpoint) offloads work to Starlette's worker thread pool, preventing event loop blocking. Combining this with `pyvips.Image.thumbnail_image` provides shrink-on-load C-level downscaling, reducing large image compression latency by ~60% to ~77%.
**Action:** Always prefer synchronous endpoints for heavy CPU image pipelines in FastAPI and leverage pyvips for lazy decoding.
