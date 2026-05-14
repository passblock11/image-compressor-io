## 2025-05-15 - [Synchronous FastAPI for CPU-bound tasks]
**Learning:** In FastAPI, using `async def` for CPU-bound tasks (like image processing with Pillow) blocks the event loop, preventing other requests from being processed. Switching to a standard `def` allows FastAPI to automatically offload the work to a thread pool, maintaining concurrency.
**Action:** Always use synchronous `def` for CPU-intensive operations in FastAPI and prefer stream-based file handling to minimize memory overhead.

## 2025-05-15 - [Stream-based file validation]
**Learning:** Loading large files fully into memory with `await file.read()` is inefficient. Using `file.file.seek(0, 2)` and `file.file.tell()` allows for constant-time file size validation without memory allocation.
**Action:** Use `file.file` directly for size validation and as an input to libraries like Pillow that support file-like objects.
