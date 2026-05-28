## 2025-05-22 - [Pillow to pyvips Migration]
**Learning:** Migrating from Pillow to `pyvips` with `thumbnail_buffer` (shrink-on-load) and switching to synchronous FastAPI endpoints for CPU-bound tasks significantly reduces latency (approx. 64% reduction).
**Action:** Always prefer `pyvips` for image processing in performance-critical paths, especially when resizing large images. Use synchronous `def` for CPU-bound FastAPI endpoints to leverage the external thread pool.
