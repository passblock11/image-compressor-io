# Bolt Performance Journal

This journal contains critical performance learnings for the image compressor service.

## 2026-03-08 - [Pillow to pyvips Migration & FastAPI Thread Pooling]
**Learning:** For CPU-bound image processing in FastAPI, migrating from Pillow to `pyvips` and changing the endpoint from an asynchronous `async def` to a synchronous `def` dramatically reduces response latencies. This ensures that FastAPI schedules the request on its external thread pool instead of blocking the main event loop. Additionally, `pyvips.Image.thumbnail_buffer` provides extreme performance benefits via "shrink-on-load" optimization, meaning only required pixels are read and processed.
**Action:** Always prefer `pyvips` with synchronous `def` endpoints in FastAPI for high-performance CPU-bound tasks, and use lazy metadata inspection (`new_from_buffer`) before invoking expensive resizing operations.
