# Bolt's Performance Journal - Image Compressor

## 2025-05-15 - Initial Performance Baseline
**Learning:** The current Pillow implementation takes ~0.21s for a 3000x2000 JPEG on the `/compress` endpoint. This is relatively slow for a simple resizing and compression task. The use of `async def` for a CPU-bound task like image processing might also be causing event loop contention under load.
**Action:** Migrate to `pyvips` for faster processing and use synchronous `def` to leverage FastAPI's thread pool.

## 2025-05-15 - Library Choice: pyvips vs Pillow
**Learning:** `pyvips` is significantly faster than Pillow, especially for resizing large images, thanks to its "shrink-on-load" feature (via `thumbnail_buffer`). This allows it to skip decoding pixels that aren't needed for the final output.
**Action:** Use `pyvips.Image.thumbnail_buffer` instead of `Image.open().resize()`.
