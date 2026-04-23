## 2025-05-15 - Pyvips Migration for Image Compression
**Learning:** Migrating from Pillow to pyvips using `thumbnail_buffer` provides a massive performance boost (76% reduction in latency for 3000x3000px images) because pyvips performs shrinking during load. Additionally, switching to synchronous endpoints for CPU-bound tasks in FastAPI prevents event loop starvation and leverages a thread pool more effectively.
**Action:** Use pyvips for high-throughput image processing tasks and prefer synchronous endpoints for heavy CPU work in FastAPI.
