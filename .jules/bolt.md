## 2025-05-14 - [High-performance image processing with pyvips]
**Learning:** Transitioning from Pillow to pyvips and using `thumbnail_buffer` for "shrink-on-load" drastically reduces image processing latency (by ~81% in this case). Synchronous endpoints in FastAPI are preferred for these CPU-bound tasks to avoid blocking the event loop.
**Action:** Use `pyvips` for image manipulation and ensure FastAPI endpoints handling these tasks are defined with `def` instead of `async def`.
