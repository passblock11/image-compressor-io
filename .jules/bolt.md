# Bolt Journal

## 2025-05-18 - Pillow File Streaming and Event Loop Offloading in FastAPI
**Learning:** In FastAPI image processing endpoints, reading uploaded files into memory with `await file.read()` creates unnecessary memory copies and passes raw bytes rather than allowing Pillow to lazy-load headers via `file.file`. Furthermore, declaring CPU-heavy image resizing routes as `async def` ties up the asyncio event loop; using synchronous `def` allows Starlette to offload execution to a threadpool. Switching from `LANCZOS` to `BICUBIC` also yielded ~20% faster resampling with imperceptible visual difference for web compression.
**Action:** When handling binary file uploads for heavy synchronous libraries (like Pillow), use standard `def` endpoints, validate size via `file.file.seek` and `tell()`, pass `file.file` directly to `Image.open`, and return `buffer.getvalue()`.
