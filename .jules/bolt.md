## 2025-05-15 - FastAPI CPU-bound Offloading
**Learning:** Using `async def` for heavy CPU-bound tasks like image processing blocks the FastAPI event loop, preventing it from handling other requests concurrently.
**Action:** Use synchronous `def` for CPU-bound endpoints; FastAPI will automatically run them in a separate thread pool.

## 2025-05-15 - Memory Efficiency with UploadFile
**Learning:** `await file.read()` loads the entire uploaded file into memory. For large files, this can lead to OOM or high memory pressure.
**Action:** Use `file.file` directly with libraries that support file-like objects (e.g., `PIL.Image.open`) to stream from disk/spool. Use `seek(0, 2)` and `tell()` for O(1) size validation.

## 2025-05-15 - Resizing RGBA vs RGB
**Learning:** Resizing images with an alpha channel (RGBA) is significantly slower (~33%) than resizing RGB images because 4 channels are processed instead of 3.
**Action:** Convert transparent images to RGB *before* resizing if the transparency is not needed (e.g., when converting to JPEG).
