## 2025-05-15 - Optimizing Image Compression with pyvips
**Learning:** Switching from Pillow to pyvips and using `thumbnail_buffer` provides a significant performance boost (~27% for large images) because it performs downsampling during decoding. Using synchronous endpoints for CPU-bound tasks in FastAPI prevents blocking the event loop.
**Action:** Prefer `pyvips` for high-throughput image processing and always use synchronous endpoints in FastAPI for heavy CPU work.
