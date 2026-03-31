## 2025-05-22 - [Optimizing Image Size Validation and Loading]
**Learning:** For `UploadFile` in FastAPI, reading the entire content with `await file.read()` for size validation and loading into `PIL.Image.open(io.BytesIO(image_bytes))` can consume twice the memory of the original image. Using `file.file.seek(0, 2)` and `file.file.tell()` for validation and passing `file.file` directly to `Image.open()` allows for memory-efficient lazy loading by Pillow.

**Action:** Always prefer seeking for size validation and passing the file stream directly to Pillow for large image processing.
