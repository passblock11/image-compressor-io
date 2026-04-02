## 2025-05-15 - [Memory-Efficient File Handling]
**Learning:** Reading `UploadFile` into memory with `await file.read()` can lead to high memory usage and even OOM errors for large images. Using `file.file.seek(0, 2)` and `tell()` allows for size validation without loading the entire file into RAM, and `PIL.Image.open(file.file)` can read the image directly from the temporary file stream.
**Action:** Always prefer using the underlying file stream for size validation and image opening to minimize memory footprint.
