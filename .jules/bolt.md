## 2025-05-15 - Initial Performance Baseline
**Learning:** Initial average latency for 3000x3000px JPEG compression using Pillow is ~0.3036s.
**Action:** Use pyvips and synchronous endpoints to reduce this latency.
## 2025-05-15 - Pyvips Migration Results
**Learning:** Migrating to pyvips with `thumbnail_buffer` and synchronous endpoints reduced latency from ~0.3036s to ~0.1173s (approx. 61% reduction) for 3000x3000px JPEGs.
**Action:** Always prefer pyvips for heavy image processing tasks in FastAPI using synchronous endpoints.
