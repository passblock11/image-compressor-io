## 2025-09-27 - Fast JPEG Downscaling and Stream Optimization in Pillow

**Learning:** Passing file streams directly to `Image.open` avoiding full memory loads, using `img.draft()` for JPEG downscaling during decode, and using sync `def` endpoints in FastAPI for CPU-bound tasks reduces image compression latency by ~75% and prevents event loop blocking.
**Action:** Use `file.file` stream seeking for file size checks, apply `img.draft()` before resizing large JPEGs, return `output.getvalue()` directly, and define CPU-bound FastAPI routes as synchronous `def`.
