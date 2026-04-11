## 2025-05-15 - Stream-based Image Handling
**Learning:** Calling `await file.read()` on a FastAPI `UploadFile` causes the file to be loaded into memory as a bytes object, doubling its memory footprint if the underlying storage has already buffered it. Stream processing via `file.file` is much more memory efficient.
**Action:** Use `file.file.seek(0, 2)` and `file.file.tell()` for size validation and pass `file.file` directly to `PIL.Image.open()`.

## 2025-05-15 - FastAPI Error Handling
**Learning:** A generic `except Exception:` block in FastAPI endpoints will swallow `HTTPException` raised within the block, masking specific error codes and messages.
**Action:** Explicitly catch and re-raise `HTTPException` before catching generic `Exception`.
