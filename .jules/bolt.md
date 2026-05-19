# Bolt's Performance Journal

## 2025-05-15 - [Migration from Pillow to pyvips]
**Learning:** Migrating to `pyvips` with `thumbnail_buffer` and switching to synchronous FastAPI endpoints for CPU-bound tasks provides a massive performance boost (~68% latency reduction). `thumbnail_buffer` is particularly effective because it performs shrink-on-load, avoiding full image decoding. Also, synchronous endpoints in FastAPI allow offloading to a thread pool, preventing event loop blockage.
**Action:** Always prefer `pyvips` for high-throughput image processing and use synchronous endpoints for heavy CPU tasks in FastAPI.
