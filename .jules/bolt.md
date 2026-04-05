## 2025-05-22 - Optimized image upload and processing
**Learning:** Calling `await file.read()` on a FastAPI `UploadFile` loads the entire file into memory as a bytes object, effectively doubling its memory footprint. Stream processing via `file.file` and using `seek`/`tell` for size validation is much more efficient.
**Action:** Always prefer `file.file` for processing `UploadFile` in FastAPI to minimize memory usage and avoid redundant data copies.
