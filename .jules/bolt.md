## 2025-03-30 - FastAPI sync def vs async def for CPU-bound Pillow image processing
**Learning:** Defining CPU-bound FastAPI endpoints as `async def` runs them directly on the main asyncio event loop, blocking concurrent requests during image operations. Defining them as synchronous `def` offloads execution to Starlette's worker thread pool, preventing event loop starvation.
**Action:** Always use synchronous `def` for CPU-bound image processing or synchronous I/O endpoints in FastAPI.

## 2025-03-30 - Pillow libjpeg draft downscaling & file-stream lazy loading
**Learning:** Calling `img.draft("RGB", (target_width, target_height))` on JPEG images before full decoding allows `libjpeg` to perform fast DCT-domain downscaling during load, reducing latency by ~70% on large JPEG inputs (e.g. from ~358ms down to ~101ms). Passing `file.file` directly to `Image.open()` avoids reading raw byte streams entirely into memory first.
**Action:** Combine `file.file` streaming with `img.draft()` for fast downscaling on large JPEG files in Pillow.
