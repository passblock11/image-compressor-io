## 2026-03-29 - [Pillow Performance: BICUBIC vs LANCZOS]
**Learning:** For resizing operations in Pillow, `Image.BICUBIC` provides a significant speedup (~30%) compared to `Image.LANCZOS` with minimal perceptual quality loss for typical web use cases.
**Action:** Default to `Image.BICUBIC` for general-purpose image resizing when performance is a priority.

## 2026-03-29 - [Efficient Image Handling in FastAPI/Pillow]
**Learning:** Reading `UploadFile` entirely into memory via `await file.read()` is inefficient for large files.
**Action:** Use `file.file` (the underlying SpooledTemporaryFile) directly with `Image.open(file.file)` to avoid redundant memory copies. For size validation, use `seek(0, 2)` and `tell()` on the stream.
