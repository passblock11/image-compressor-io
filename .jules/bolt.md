## 2025-05-22 - [Optimizing Image Compression with pyvips]
**Learning:** Migrating from Pillow to pyvips and switching to a synchronous FastAPI endpoint for CPU-bound tasks results in significant performance gains (~75% reduction in latency for large images). Using `thumbnail_buffer` instead of full load followed by resize is a key optimization in pyvips.
**Action:** Always prefer pyvips for high-volume image processing and ensure CPU-bound FastAPI endpoints are synchronous to leverage the thread pool.
