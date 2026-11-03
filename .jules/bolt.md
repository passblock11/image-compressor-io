# Bolt's Performance Journal

## 2026-03-08 - FastAPI Thread Pool & Direct Stream Resampling for CPU-bound Image Services
**Learning:** Defining CPU-bound FastAPI endpoints (such as image decoding, resampling, and compression) as `async def` runs them directly on the asyncio event loop, causing request head-of-line blocking under load. Using synchronous `def` routes image processing to Starlette's external thread pool (`anyio.to_thread.run_sync`). Additionally, directly validating upload size via `file.file.seek` / `tell` avoids copying the full payload into memory, and `Image.BICUBIC` resampling reduces resizing latency by ~20-25% compared to `Image.LANCZOS` with virtually indistinguishable visual quality.
**Action:** When working on CPU-heavy FastAPI endpoints, prefer synchronous `def` over `async def`, stream directly into image decoders instead of loading full byte arrays in memory, and use `Image.BICUBIC` for downscaling.
