## 2025-05-15 - Pyvips Migration for Performance
**Learning:** Transitioning from Pillow to pyvips with `thumbnail_buffer` and synchronous endpoints significantly reduces latency for image processing in FastAPI. Using `file.file.seek(0, 2)` and `tell()` allows for efficient file size validation without loading the entire file into memory prematurely.
**Action:** Always prefer pyvips for heavy image processing tasks and use stream-based file validation for large uploads.
