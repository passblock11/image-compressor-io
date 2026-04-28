## 2024-05-15 - [Migration to pyvips]
**Learning:** Transitioning from Pillow to pyvips for image processing, combined with synchronous FastAPI endpoints for CPU-bound tasks, significantly reduces latency. `pyvips.Image.thumbnail_buffer` is particularly effective for fast resizing during load.
**Action:** Use pyvips for high-performance image processing needs and prefer synchronous endpoints for CPU-bound work in FastAPI to leverage the built-in thread pool.
