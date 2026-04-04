## 2025-04-04 - [Memory & Speed Optimization in Image Processing]
**Learning:** Using `await file.read()` in FastAPI with `UploadFile` reads the entire file into memory twice (once by Starlette, once into your variable). For image processing, this can lead to memory exhaustion on large files. Furthermore, using `Image.LANCZOS` for resizing is significantly slower than `Image.BICUBIC` for a marginal quality gain in most web scenarios. Also, catch-all `except Exception:` blocks in FastAPI endpoints can swallow `HTTPException`, leading to generic 400 errors instead of specific validation messages.

**Action:**
1. Use `file.file.seek(0, 2)` and `tell()` to validate file size without reading it.
2. Pass `file.file` directly to `Image.open()` to avoid redundant copies.
3. Use `Image.BICUBIC` for resizing when extreme quality is not the primary concern.
4. Explicitly catch and re-raise `HTTPException` before catching generic `Exception`.
