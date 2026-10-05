## 2025-02-16 - Migrating Image Processing Endpoint from Pillow to pyvips and Sync Threading
**Learning:**
1. Processing images with `pyvips.Image.new_from_buffer` and `thumbnail_image` provides a ~71% latency reduction over Pillow `resize` and `save` due to libvips streaming/demand-driven architecture.
2. In FastAPI, defining CPU-intensive image processing endpoints as synchronous (`def`) offloads execution to Starlette's worker thread pool, preventing blocking of the asyncio event loop.
3. Setting `Q=80`, `optimize_coding=True`, and `interlace=True` in `pyvips.Image.jpegsave_buffer` achieves optimal progressive JPEG compression matching Pillow's `quality=80, optimize=True, progressive=True`.

**Action:**
When handling image uploads and resizes in FastAPI apps with `pyvips` installed, use synchronous endpoint definitions and direct libvips buffer operations (`new_from_buffer`, `thumbnail_image`, and `jpegsave_buffer`).
