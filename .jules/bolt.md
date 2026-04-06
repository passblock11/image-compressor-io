## 2025-05-15 - Stream-based processing for FastAPI UploadFile
**Learning:** Calling `await file.read()` on a FastAPI `UploadFile` (which wraps a SpooledTemporaryFile) duplicates the file in memory. Using `file.file.seek(0, 2)` and `tell()` allows for efficient size validation without memory overhead. Passing `file.file` directly to `PIL.Image.open()` also avoids unnecessary byte copies.
**Action:** Use stream processing via `file.file` for efficient file handling in FastAPI.

## 2025-05-15 - Exception handling in FastAPI
**Learning:** A catch-all `except Exception:` block will swallow `HTTPException` and convert them into generic 500 (or in this case 400) errors if not handled correctly.
**Action:** Explicitly catch and re-raise `HTTPException` before the general exception block.
