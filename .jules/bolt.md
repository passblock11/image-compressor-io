# Bolt Performance Journal

## 2025-05-22 - Image Compression Baseline
**Learning:** The current implementation uses Pillow with `optimize=True`, `progressive=True`, and `LANCZOS` resampling. It runs in an `async def` FastAPI endpoint, which might block the event loop since image processing is CPU-bound.
**Action:** Baseline performance for a 3000x3000px red JPEG is ~0.303s.

## 2025-05-22 - pyvips Migration & Sync Endpoint
**Learning:** Migration to `pyvips` using `thumbnail_buffer` and switching to a synchronous FastAPI endpoint resulted in a ~68% reduction in average latency (from 0.30s to 0.096s) for large images. `pyvips.Image.thumbnail_buffer` is significantly more efficient than loading the full image and then resizing.
**Action:** Use `pyvips` for image processing tasks and synchronous endpoints for CPU-bound tasks in FastAPI to leverage the external thread pool.
