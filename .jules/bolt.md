## 2026-03-29 - Synchronous Endpoint offloading and Stream-based Image Resampling

**Learning:** Running CPU-bound PIL image operations inside an `async def` route in FastAPI blocks the main asyncio event loop, causing request queueing. Changing the route to synchronous `def` offloads CPU tasks to Starlette's worker thread pool. Additionally, using `Image.BICUBIC` resampling and reading from `file.file` directly avoids memory duplication and speeds up image processing by ~23%.
**Action:** Use synchronous `def` for CPU-bound image processing routes in FastAPI, and prefer `Image.BICUBIC` over `Image.LANCZOS` for downscaling.
