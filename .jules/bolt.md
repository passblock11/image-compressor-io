## 2025-05-11 - [Migrating to pyvips and synchronous endpoints]
**Learning:** Transitioning from Pillow to pyvips for image processing significantly reduces latency for large images. Additionally, using synchronous `def` instead of `async def` in FastAPI for CPU-bound tasks like image compression allows the work to be offloaded to a thread pool, preventing the event loop from being blocked and improving overall throughput.
**Action:** Always prefer `pyvips` with `thumbnail_buffer` for high-performance image resizing and use synchronous endpoints for heavy CPU work in FastAPI.

## 2025-05-11 - [Repository Hygiene]
**Learning:** Tools like `pytest` and `ruff` can generate cache directories (`.pytest_cache`, `.ruff_cache`) and Python can generate bytecode (`__pycache__`, `.pyc`). These artifacts should not be included in a PR as they clutter the repository and are environment-specific.
**Action:** Ensure all temporary files, cache directories, and bytecode are removed before submitting a change.
