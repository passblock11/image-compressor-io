## 2025-06-16 - [FastAPI Async vs Sync for CPU Tasks]
**Learning:** Using `async def` for CPU-bound tasks (like image processing) blocks the FastAPI event loop, limiting concurrency. Switching to a standard `def` allows FastAPI to delegate the work to an external thread pool, improving throughput.
**Action:** Use `def` instead of `async def` for image processing or other heavy CPU tasks in FastAPI.

## 2025-06-16 - [pyvips for High-Performance Image Resizing]
**Learning:** `pyvips.Image.thumbnail_buffer` provides a significant speed advantage (up to 3x in this case) over Pillow by performing "shrink-on-load", which reads only the pixels required for the target size.
**Action:** Prefer `pyvips` with "shrink-on-load" for resizing large images in performance-critical paths.
