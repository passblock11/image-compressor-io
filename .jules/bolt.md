# Bolt's Journal

## 2025-07-30 - High-performance Image Resizing and File Upload Validation
**Learning:** Using `pyvips.Image.thumbnail_buffer` with FastAPI's synchronous thread pool delivers immense speed-ups for image processing. By leveraging `file.file.seek(0, io.SEEK_END)` and `file.file.tell()`, we can perform file size validation completely without reading the upload into memory first, mitigating memory denial-of-service risks. Using `pyvips`'s lazy metadata reading via `new_from_buffer` and shrink-on-load via `thumbnail_buffer` ensures optimal latency and CPU utilization.
**Action:** Always prefer synchronous def endpoints in FastAPI for CPU-bound tasks like image manipulation, utilize `seek`/`tell` for instant payload-size checks, and use `pyvips`'s shrink-on-load optimization for high-throughput resizing.
