## 2026-03-08 - Fast pyvips Migration & FastAPI Synchronous Endpoint Thread Pooling

**Learning:** Replacing Pillow with pyvips in image processing endpoints reduces CPU processing latency by ~25-40% due to C-based libvips demand-driven execution and optimized downscaling. Furthermore, defining CPU-intensive FastAPI endpoints as synchronous `def` instead of `async def` offloads execution from the main asyncio event loop to Starlette's thread pool, preventing event loop blocking during heavy image decoding/compression. In addition, checking file size via file stream position seeking (`seek(0, SEEK_END)`) avoids memory allocation for invalid or oversized payloads.

**Action:** When working on CPU-heavy image endpoints in FastAPI, prefer pyvips over Pillow and define endpoints as synchronous `def` functions to enable thread pool execution. Always handle `HTTPException` re-raising explicitly before generic exception handlers to preserve status codes.
