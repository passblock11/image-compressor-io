## 2025-05-20 - pyvips vs Pillow for Image Compression Endpoint

**Learning:** Migrating from Pillow to pyvips with `thumbnail_image` and `jpegsave_buffer` reduces image processing latency by 50-70% on large images. Additionally, defining CPU-bound FastAPI endpoints as synchronous `def` offloads work to Starlette's worker threadpool, preventing blocking of the asyncio event loop.
**Action:** Use pyvips with fallback for image processing services and ensure CPU-heavy FastAPI endpoints are sync `def`.
