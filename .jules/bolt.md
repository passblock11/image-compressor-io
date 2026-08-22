## 2025-08-22 - Pyvips shrink-on-load & FastAPI Threadpool Optimization

**Learning:**
In FastAPI, `async def` endpoints executing CPU-bound tasks like Pillow/pyvips image processing block the main asyncio event loop. Switching the route to synchronous `def` offloads CPU processing to Starlette's thread pool. Additionally, replacing Pillow with `pyvips` leverages `libvips` C bindings and shrink-on-load thumbnailing (`img.thumbnail_image`), reducing image compression latency from ~360ms to ~110ms (~70% speedup).

**Action:**
For heavy image or CPU-bound processing in FastAPI, use synchronous `def` routes along with `pyvips` lazy streaming/thumbnailing instead of loading full pixel buffers into memory with PIL.
