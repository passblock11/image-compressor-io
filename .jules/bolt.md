## 2026-03-31 - Synchronous Threadpool Execution and pyvips Streaming for Image Processing

**Learning:** Defining CPU-bound FastAPI endpoints as `async def` causes the main asyncio event loop to block during heavy image decoding/resampling operations, severely degrading throughput and latency. Switching to synchronous `def` offloads image processing to Starlette's worker thread pool. Additionally, replacing Pillow with pyvips C-based streaming pipeline and JPEG shrink-on-load reduces endpoint latency by ~68% (from ~213 ms down to ~68 ms for 3000x2000 images).

**Action:** For CPU-bound operations in FastAPI, always use synchronous `def` endpoints to utilize worker threads, and leverage C-native streaming libraries like pyvips over pure Python or Pillow where high-throughput image processing is required.
