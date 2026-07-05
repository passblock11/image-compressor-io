## 2025-05-15 - [Library Migration to pyvips]
**Learning:** Migrating the image compression endpoint from Pillow to pyvips and switching to a synchronous `def` endpoint reduced average latency from ~0.31s to ~0.10s (approx. 67% reduction) for a 3000x3000px JPEG. The use of `thumbnail_buffer` provides significant 'shrink-on-load' optimization, especially for large images.
**Action:** Prefer pyvips for high-performance image processing tasks, particularly when resizing large files.
