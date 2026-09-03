## 2025-03-05 - pyvips Migration & FastAPI Worker Thread Pools
**Learning:** Replacing Pillow with `pyvips` for image resize/compression reduced endpoint processing latency by ~46% to ~70% on large images. Additionally, defining CPU-intensive image processing endpoints as synchronous `def` in FastAPI ensures Starlette delegates execution to a threadpool rather than blocking the main `asyncio` event loop.
**Action:** When working on FastAPI services with heavy C-binding image manipulation libraries, prefer `pyvips` with synchronous `def` routes for maximum throughput and low latency.
