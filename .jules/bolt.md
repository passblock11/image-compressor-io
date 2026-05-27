
## 2025-05-22 - [Pillow to pyvips Migration]
**Learning:** Migrating from Pillow to pyvips and switching the FastAPI endpoint from 'async def' to synchronous 'def' significantly reduces latency for CPU-bound image processing tasks. Synchronous endpoints prevent the event loop from being blocked and allow FastAPI to use an external thread pool. Using 'thumbnail_buffer' for shrink-on-load further optimizes memory and speed.
**Action:** Always prefer pyvips for heavy image processing if available. Ensure dependencies (libvips-dev) are correctly documented in build configurations (e.g., render.yaml).
