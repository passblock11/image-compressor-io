## 2025-05-15 - Image processing optimization with pyvips

**Learning:** Replacing Pillow with `pyvips` for image processing tasks like resizing and compression provides a significant performance boost (~2.4x speedup). Using `pyvips.Image.thumbnail_buffer` is particularly effective as it leverages shrink-on-load to reduce memory usage and processing time. Additionally, for CPU-bound tasks in FastAPI, using synchronous `def` allows the framework to offload work to a thread pool, preventing the event loop from being blocked.

**Action:** Prefer `pyvips` over Pillow for high-performance image processing when system dependencies allow. Use synchronous endpoints for CPU-intensive tasks in FastAPI.
