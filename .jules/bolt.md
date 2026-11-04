# Bolt's Performance Journal

## 2026-03-08 - FastAPI Threadpool Offloading & Resampling Efficiency
**Learning:** Defining CPU-bound FastAPI endpoints as `async def` runs them directly on the main event loop, causing heavy operations like Pillow image resizing to block concurrent request handling. Switching to standard synchronous `def` tells FastAPI/Starlette to execute the route in an external worker threadpool. Furthermore, using `file.file.seek(0, io.SEEK_END)` to inspect file size before passing `file.file` directly to `Image.open` avoids redundant in-memory byte copies. Switching downscaling resampling from `LANCZOS` to `BICUBIC` provides ~15-25% faster downscaling latency with visually indistinguishable output for Web JPEG compression.
**Action:** For CPU-bound endpoints in FastAPI services handling image processing, use synchronous route definitions, direct stream ingestion, and benchmark resampling filters to balance processing throughput and visual fidelity.
