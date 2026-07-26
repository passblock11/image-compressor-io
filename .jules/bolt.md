# Bolt's Performance Journal

## 2025-07-26 - CPU-bound Operations Block the FastAPI Event Loop
**Learning:** Declaring CPU-bound image processing tasks under `async def` runs them on the main FastAPI event loop, causing any active image compression to completely block all concurrent request processing. Moving the endpoint to standard synchronous `def` offloads execution to FastAPI's internal `ThreadPoolExecutor`, preventing blocking.
**Action:** Always use synchronous `def` endpoints for CPU-bound tasks in FastAPI (such as image resizing, heavy parsing, or cryptography) so they are offloaded to threads.

## 2025-07-26 - In-Memory File Size Validation Overheads
**Learning:** Reading a file entirely into memory via `await file.read()` before checking its length causes significant memory pressure for large files (up to the 100MB limit). Checking length via standard file object manipulation `seek(0, io.SEEK_END)` and `tell()` allows instant rejection of oversized uploads before wasting system memory.
**Action:** Use `.seek(0, io.SEEK_END)` and `.tell()` on FastAPI's underlying `UploadFile.file` object to perform O(1) file size checks.

## 2025-07-26 - Pyvips High-Performance Image Processing and Shrink-On-Load
**Learning:** Migrating from Pillow to `pyvips` drastically reduces image processing latency by utilizing libvips. Specifically, `pyvips.Image.thumbnail_buffer` provides extreme speedups by performing "shrink-on-load" optimizations, which decodes only the fraction of source image pixels required for the final dimensions rather than reading the entire source file.
**Action:** When working with libvips / pyvips for resizing large images, load buffers via `thumbnail_buffer` to perform shrink-on-load.
