## 2025-05-15 - [Library Migration: Pillow to pyvips]
**Learning:** Migrating from Pillow to pyvips for image processing (resizing and JPEG compression) provides a massive performance boost (up to 75% latency reduction) by leveraging libvips stream-based processing and "shrink-on-load" optimizations.
**Action:** Use `pyvips.Image.thumbnail_buffer` instead of full loading and resizing for maximum efficiency.

## 2025-05-15 - [FastAPI CPU-Bound Tasks]
**Learning:** For CPU-intensive tasks like image processing, using FastAPI synchronous `def` endpoints is more efficient than `async def`. FastAPI automatically runs `def` routes in an external thread pool, preventing the event loop from being blocked.
**Action:** Define CPU-bound endpoints as `def` rather than `async def` in FastAPI.
