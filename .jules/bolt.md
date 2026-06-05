## 2025-05-22 - [Pyvips Migration for Image Compression]
**Learning:** Migrating from Pillow to pyvips and switching from `async def` to synchronous `def` in FastAPI results in a massive (~68-70%) reduction in latency for high-resolution image processing. `thumbnail_buffer` is particularly effective for large images as it performs shrink-on-load.
**Action:** Always prefer `pyvips` for heavy image processing tasks and use synchronous endpoints in FastAPI to delegate CPU-bound work to the thread pool.

## 2025-05-22 - [Stream-based File Size Validation]
**Learning:** In FastAPI, `UploadFile.file.seek(0, io.SEEK_END)` followed by `tell()` is a zero-cost way to validate file size without reading the entire payload into memory.
**Action:** Use this pattern for early size validation in upload endpoints.
