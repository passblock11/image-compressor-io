## 2025-05-15 - FastAPI Performance Pattern for CPU-bound tasks
**Learning:** Using synchronous `def` instead of `async def` for CPU-bound tasks like image processing in FastAPI allows the framework to automatically execute them in a separate thread pool. This prevents blocking the event loop and improves overall responsiveness and throughput.
**Action:** Always use synchronous `def` for image processing or other heavy computation endpoints in FastAPI.

## 2025-05-15 - Efficient File Size Validation
**Learning:** Validating `UploadFile` size by seeking to the end of the stream (`file.file.seek(0, 2)`) and using `tell()` avoids reading the entire file into RAM, saving memory and time for large uploads.
**Action:** Use `seek(0, 2)` and `tell()` for early file size validation in FastAPI endpoints.

## 2025-05-15 - Pyvips vs Pillow for Resizing
**Learning:** `pyvips.Image.thumbnail_buffer` is significantly faster than opening a full image with Pillow and then resizing, because it only decodes the pixels needed for the thumbnail size.
**Action:** Use `thumbnail_buffer` or `thumbnail_image` in pyvips for high-performance resizing.
