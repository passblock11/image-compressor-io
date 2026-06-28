# Bolt ⚡ Performance Journal

## 2025-02-14 - Migrated Image Compression to pyvips

**Learning:** Migrating from Pillow to `pyvips` significantly improves image processing performance. The key performance gains come from:
1.  **Shrink-on-load:** `pyvips.Image.thumbnail_buffer` only reads the pixels required for the target size from the source file, rather than decoding the entire high-resolution image first.
2.  **Thread Pool Utilization:** Switching from `async def` to synchronous `def` in FastAPI allows the framework to delegate CPU-bound work (like image compression) to an external thread pool, preventing event loop blockage and improving concurrent throughput.
3.  **Low-level optimization:** `libvips` is a low-level library designed for high performance and low memory usage, outperforming Pillow in most resizing and compression tasks.

**Action:** Prefer `pyvips` for image-heavy processing tasks. Always use synchronous endpoints in FastAPI for CPU-bound tasks like image manipulation to avoid blocking the main event loop.

### Benchmark Results (3000x3000px JPEG)
- **Before (Pillow, async):** ~0.4047s
- **After (pyvips, sync):** ~0.1040s (~74.3% improvement)
