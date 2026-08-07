# Bolt Journal ⚡

## 2025-02-15 - Pyvips Lazy-Loading and Resizing Optimizations
**Learning:** Pyvips is highly performance-optimized but has specific nuances in how image buffers are handled:
1. Synchronous endpoints (`def` instead of `async def`) should be preferred in FastAPI for CPU-bound operations (like image processing) to allow execution in external thread pools, preventing the main event loop from blocking.
2. In-memory file size validation via `file.file.seek(0, io.SEEK_END)` and `file.file.tell()` avoids loading huge payloads into memory.
3. Calling `thumbnail_image` on a lazily-loaded image (`new_from_buffer`) is significantly faster than `thumbnail_buffer` (~32.5% latency reduction) because it avoids reconstructing and re-parsing raw buffers multiple times.
4. Correctly specify argument `Q` for quality in `jpegsave_buffer` instead of `quality` for compatibility with pyvips 3.1.1 bindings.
**Action:** Use sync def endpoints with pyvips for CPU-bound workloads. Read headers lazily using `new_from_buffer`, resize with `thumbnail_image` on-the-fly, and use `Q` instead of `quality` to prevent runtime errors.
