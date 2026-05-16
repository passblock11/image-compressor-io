## 2025-05-15 - [Pillow Performance Tuning]
**Learning:** Switching from `async def` to `def` in FastAPI for CPU-bound Pillow operations prevents event loop blocking and improves throughput. `Image.Resampling.BICUBIC` is significantly faster than `LANCZOS` with minimal quality loss. Streaming the file directly into `Image.open()` avoids unnecessary memory copies.
**Action:** Always prefer synchronous endpoints for heavy image processing in FastAPI and use BICUBIC for web-standard resizing.
