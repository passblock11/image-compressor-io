## 2025-05-15 - [Library Migration to pyvips]
**Learning:** Migrating from Pillow to pyvips for JPEG compression and using `thumbnail_buffer` (shrink-on-load) significantly reduces latency (~42% in this codebase). Switching FastAPI endpoints to synchronous `def` for CPU-bound tasks prevents event loop blockage by utilizing the internal thread pool.
**Action:** Always prefer `pyvips` for high-volume image processing when system dependencies are available. Ensure `libvips-dev` is in the build environment. Use `def` for image processing endpoints in FastAPI.
