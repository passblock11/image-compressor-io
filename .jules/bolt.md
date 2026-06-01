## 2025-06-01 - [FastAPI CPU-bound Endpoint & pyvips Migration]
**Learning:** Migrating from Pillow to pyvips and switching from 'async def' to 'def' for CPU-bound image processing in FastAPI provides a massive latency reduction (~77%). pyvips's 'thumbnail_buffer' is particularly effective as it performs shrink-on-load.
**Action:** Always check for 'pyvips' and 'libvips' availability in image processing tasks. Prefer synchronous endpoints for heavy CPU work in FastAPI to avoid event loop blockage.
