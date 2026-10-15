## 2025-10-15 - FastAPI CPU-Bound Thread Offloading & Pyvips Optimization
**Learning:** Defining CPU-bound image processing routes as synchronous `def` instead of `async def` offloads execution to Starlette's worker thread pool, preventing blocking of FastAPI's asyncio event loop. Additionally, using `pyvips` thumbnailing and progressive JPEG buffer exporting provides up to 5.5x latency reduction over standard Pillow processing.
**Action:** Always use synchronous `def` for CPU-bound image transformations in FastAPI, and leverage pre-existing `pyvips` bindings for image scaling and encoding.
