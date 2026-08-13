## 2025-02-18 - Python pyvips Lazy-Loading and Endpoint Thread Pool Optimization
**Learning:**
1. Changing the FastAPI endpoint signature from `async def` to synchronous `def` for heavy CPU-bound image tasks is crucial, as FastAPI runs synchronous handlers in an external thread pool to prevent blocking the event loop.
2. In pyvips, `new_from_buffer` lazily loads metadata. If resizing is required, using `thumbnail_image` on the opened Image is significantly faster than `thumbnail_buffer` because it avoids loading or recreating the buffer from scratch twice.
3. Catching broad `Exception` in Python can swallow `HTTPException` (which inherits from `Exception`). It is essential to capture or re-raise `HTTPException` first.

**Action:**
- Always define CPU-bound endpoints as synchronous `def` in FastAPI.
- Use `new_from_buffer` to inspect properties lazily and apply `thumbnail_image` rather than `thumbnail_buffer` to avoid duplicate reads.
- Explicitly re-raise `HTTPException` before general `Exception` handlers in try/except blocks.
