## 2025-02-17 - FastAPI Sync Threadpool and Pillow Direct Stream Decoding

**Learning:**
1. CPU-bound image manipulation in FastAPI endpoints should use synchronous `def` instead of `async def`. Defining as synchronous offloads processing to Starlette's worker threadpool, preventing heavy computations from blocking the main asyncio event loop.
2. Passing `file.file` directly to Pillow's `Image.open()` avoids reading and copying the entire payload in memory as a byte string (`await file.read()`).
3. Switching image resampling from `Image.LANCZOS` to `Image.BICUBIC` reduces image resizing latency by ~20-26% for large images with virtually identical visual quality.

**Action:**
Always check if CPU-bound FastAPI handlers are unnecessarily defined as `async def` and ensure binary upload streams are passed directly to decoders without pre-buffering into memory.
