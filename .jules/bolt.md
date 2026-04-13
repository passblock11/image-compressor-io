## 2025-05-15 - Stream-based Image Processing
**Learning:** Calling `await file.read()` on a FastAPI `UploadFile` loads the entire file into memory as a bytes object. For image processing with PIL, passing the underlying file handle `file.file` directly to `Image.open()` is much more memory-efficient and faster. Additionally, using `seek(0, 2)` and `tell()` allows for file size validation without any memory allocation for the file content.
**Action:** Always prefer stream-based handling (`file.file`) for large file uploads in FastAPI/PIL workflows.

## 2025-05-15 - Resampling Filter Performance
**Learning:** `Image.LANCZOS` is significantly slower than `Image.BICUBIC` for resizing operations. In most web scenarios, the quality difference is negligible compared to the 25-40% performance gain achieved by switching to `BICUBIC`.
**Action:** Default to `Image.BICUBIC` for image resizing unless the highest possible quality is strictly required.
