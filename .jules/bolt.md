# Bolt's Performance Journal

## 2025-05-18 - High-Efficiency Image Compression with PyVips and Stream Size Validation
**Learning:** Utilizing `pyvips`'s C-based shrink-on-load pipeline reduces JPEG resize and compression latency by ~62% compared to Pillow. Furthermore, validating FastAPI UploadFile sizes using stream seeking (`file.file.seek(0, io.SEEK_END)`) avoids reading large file payloads upfront into Python memory. Finally, defining CPU-bound endpoints as synchronous `def` offloads execution to Starlette worker threads, keeping the asyncio event loop unblocked.
**Action:** Always check stream size with $O(1)$ file seeking before reading payloads, offload heavy CPU image tasks to worker threads in FastAPI, and use libvips bindings (`pyvips`) when pre-configured in project dependencies.
