## 2025-05-14 - Migrating to pyvips for Image Processing

**Learning:** Migrating from Pillow to pyvips (libvips) provides massive performance gains for image processing tasks like resizing and compression. Specifically, using `thumbnail_buffer` enables "shrink-on-load" optimization, which significantly reduces memory usage and processing time by only decoding the required pixels for the target size. Additionally, switching the CPU-bound FastAPI endpoint from `async def` to synchronous `def` prevents blocking the event loop and leverages FastAPI's internal thread pool for better throughput.

**Action:** Prefer `pyvips` over `Pillow` for high-throughput image processing. Ensure `libvips-dev` is present in the environment (e.g., via `render.yaml`). Use `def` for CPU-bound tasks in FastAPI.
