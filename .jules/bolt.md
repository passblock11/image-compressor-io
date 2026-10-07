## 2025-05-18 - High-performance Image Resizing with pyvips in FastAPI
**Learning:**
- Libvips (`pyvips`) provides 2-4x speedup and significantly lower memory footprint compared to Pillow for image thumbnailing and compression, especially on large images, due to libvips's streaming pipeline architecture and shrink-on-load capability.
- Defining CPU-bound FastAPI endpoints as synchronous (`def` instead of `async def`) offloads image processing to Starlette's worker thread pool, preventing CPU-intensive processing from blocking the asyncio event loop.
- When saving JPEGs with pyvips, `jpegsave_buffer(Q=80, optimize_coding=True, interlace=True)` produces progressive JPEGs with optimized Huffman tables equivalent to Pillow's `quality=80, optimize=True, progressive=True`.

**Action:**
- Utilize `pyvips.Image.new_from_buffer` and `thumbnail_image` for image resizing.
- Convert CPU-bound endpoints in FastAPI to standard `def` functions to leverage thread pools.
