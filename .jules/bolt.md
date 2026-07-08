## 2025-05-15 - [Migration from Pillow to pyvips]
**Learning:** Migrating from Pillow to `pyvips` with `thumbnail_buffer` (shrink-on-load) provides a massive performance boost (~68% latency reduction) for image resizing and compression. Additionally, using synchronous `def` for CPU-bound FastAPI endpoints allows delegating work to a thread pool, preventing event loop blockage and improving throughput.
**Action:** Always check if `pyvips` and `libvips` are available when optimizing image processing pipelines. Prefer `thumbnail_buffer` for resizing large images.
