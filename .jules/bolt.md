## 2025-05-15 - Pillow JPEG draft downscaling and stream processing
**Learning:** Calling `img.draft('RGB', size)` before decoding JPEGs enables libjpeg fast downscaling, reducing decode & resize latency by ~72% on large images. Passing `file.file` directly to `Image.open` and checking stream size with `seek`/`tell` avoids reading the entire payload into RAM.
**Action:** Always leverage `img.draft` for JPEG downscaling in Pillow, open streams directly, and run CPU-bound Pillow tasks in synchronous `def` endpoints so FastAPI offloads them to worker threads.
