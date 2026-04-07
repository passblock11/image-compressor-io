## 2025-05-15 - Initial Performance Journal
**Learning:** The application reads the entire image into memory using `await file.read()`, which is inefficient for large files and duplicates memory usage.
**Action:** Use `file.file` (the underlying SpooledTemporaryFile) directly with `Image.open()` to stream the file.

**Learning:** `Image.LANCZOS` is used for resizing. While high quality, it is slower than `Image.BICUBIC`.
**Action:** Consider using `Image.BICUBIC` if the quality difference is negligible for the use case.

**Learning:** `pyvips` is in `requirements.txt` but not used in `app.py`. libvips is generally much faster than Pillow for image processing.
**Action:** Investigate if switching to `pyvips` provides a significant performance boost.
