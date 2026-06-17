## 2025-05-22 - [Optimizing image compression with pyvips]
**Learning:** Migrating the image compression endpoint from Pillow to pyvips and switching from `async def` to synchronous `def` significantly reduced latency (by ~65%). pyvips provides superior performance for resizing and saving, especially when using 'shrink-on-load' optimizations like `thumbnail_buffer`.
**Action:** Prefer pyvips over Pillow for high-throughput image processing tasks. When using FastAPI for CPU-bound tasks, use synchronous `def` to avoid blocking the event loop and leverage FastAPI's thread pool.

## 2025-05-22 - [Efficient file size validation]
**Learning:** For FastAPI `UploadFile`, you can validate file size without reading the entire content into memory by seeking to the end of the underlying file object.
**Action:** Use `file.file.seek(0, io.SEEK_END)`, `file.file.tell()`, and `file.file.seek(0)` for efficient file size checks.
