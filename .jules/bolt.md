## 2025-10-08 - FastAPI Threadpool Offloading & pyvips Acceleration
**Learning:** Defining CPU-bound image processing endpoints as `async def` blocks the FastAPI/asyncio event loop, causing severe request queuing. Using synchronous `def` offloads CPU work to Starlette's worker thread pool. Furthermore, utilizing `pyvips` for C-level image streaming/thumbnailing cuts image processing latency by ~63.8% compared to Pillow.
**Action:** Always use synchronous `def` for heavy CPU/image-processing endpoints in FastAPI, and use libvips bindings (`pyvips`) when available.
