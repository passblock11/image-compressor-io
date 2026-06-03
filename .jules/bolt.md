## 2025-06-03 - Migrating Image Compression to pyvips
**Learning:** Migrating from Pillow to pyvips for JPEG compression and resizing can yield massive performance gains (~70% latency reduction). Switching to a synchronous FastAPI endpoint allows the application to utilize an external thread pool for CPU-bound tasks, preventing event loop blockage. Stream-based file size validation avoids redundant memory allocation for large uploads.
**Action:** Always consider pyvips for high-performance image processing in Python. Ensure libvips-dev is available in the environment.
