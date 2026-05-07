## 2025-05-23 - Migration to pyvips for high-performance image processing

**Learning:** Migrating from Pillow to pyvips and switching from `async def` to `def` (synchronous) endpoints in FastAPI for CPU-bound tasks like image compression resulted in a ~68% latency reduction. `pyvips.Image.thumbnail_buffer` is particularly effective because it performs "shrink-on-load", decoding only the necessary pixels for the target size.

**Action:** Prefer `pyvips` for heavy image processing tasks. For CPU-bound operations in FastAPI, use synchronous `def` to leverage the internal thread pool and avoid blocking the event loop.

## 2025-05-23 - FastAPI Error Handling with broad except blocks

**Learning:** Using a catch-all `except Exception:` block in FastAPI endpoints can swallow `HTTPException` raised within the `try` block, leading to generic 400 or 500 errors instead of the intended specific status codes and details.

**Action:** Always explicitly catch and re-raise `HTTPException` before a general `except Exception:` block to ensure custom error responses are preserved.
