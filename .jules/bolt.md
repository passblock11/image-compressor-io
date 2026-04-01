## 2025-05-15 - [Efficient File Size Validation in FastAPI]
**Learning:** Using `await file.read()` in FastAPI to validate file size or open images reads the entire file into memory (RAM). For large files (e.g., 100MB), this creates a significant memory bottleneck.
**Action:** Use `file.file.seek(0, 2)` to reach the end of the stream and `file.file.tell()` to get the size in bytes. Then `seek(0)` to reset the pointer for processing.

## 2025-05-15 - [Direct Stream Access for PIL]
**Learning:** `PIL.Image.open()` can accept a file-like object directly. Passing `file.file` (the underlying `SpooledTemporaryFile`) avoids creating an intermediate `io.BytesIO` buffer, further reducing memory usage.
**Action:** Pass `file.file` directly to `Image.open()` instead of reading bytes into a buffer first.
