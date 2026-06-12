## 2025-05-22 - [pyvips thumbnail_buffer limitations]
**Learning:** In pyvips version 3.1.1 (and some other environments), `pyvips.Image.thumbnail_buffer` does not support the `no_upscale` optional argument. Additionally, `jpegsave_buffer` may not support `subsampling_mode`.
**Action:** Always check capabilities or dimensions before calling thumbnailing if upscaling should be avoided. Use `new_from_buffer` to lazily check width/height.

## 2025-05-22 - [FastAPI CPU-bound concurrency]
**Learning:** Using `async def` for CPU-bound tasks like image processing blocks the FastAPI event loop, preventing it from handling other requests.
**Action:** Use synchronous `def` for CPU-bound endpoints to allow FastAPI to delegate the work to an external thread pool.
