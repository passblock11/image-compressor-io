## 2025-05-22 - [FastAPI CPU-bound Endpoint & pyvips Migration]
**Learning:** For CPU-bound tasks like image processing in FastAPI, using a synchronous `def` endpoint instead of `async def` allows FastAPI to offload work to a separate thread pool, preventing the event loop from blocking and significantly improving performance. Additionally, `pyvips` (using `thumbnail_buffer`) provides a massive speedup (~75% latency reduction) over `Pillow` for large image operations.
**Action:** Always use synchronous `def` for CPU-intensive endpoints in FastAPI and prefer `pyvips` for high-performance image processing when available in the environment.

## 2025-05-22 - [Efficient File Size Validation]
**Learning:** Reading an entire `UploadFile` into memory just for size validation is inefficient. Using `file.file.seek(0, 2)` and `file.file.tell()` allows for O(1) size validation without increasing memory pressure.
**Action:** Use `seek`/`tell` on the underlying file object of `UploadFile` for early size checks.

## 2025-05-22 - [FastAPI Error Handling Anti-pattern]
**Learning:** Using a broad `except Exception:` block in a FastAPI endpoint can swallow `HTTPException` raised within the `try` block, leading to incorrect status codes (e.g., 500 or 400 instead of 413) being returned to the client.
**Action:** Explicitly catch and re-raise `HTTPException` before a generic `except` block to ensure accurate error reporting.
