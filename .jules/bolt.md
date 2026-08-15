## 2026-08-15 - Fast Image Processing with pyvips in FastAPI
**Learning:** `pyvips` leverages libvips's demand-driven streaming architecture and shrink-on-load capabilities, reducing image compression execution latency by ~60%-78% on large images compared to Pillow. Offloading CPU-bound `pyvips` execution to FastAPI's thread pool via synchronous `def` routes avoids blocking the asyncio event loop.
**Action:** Use `pyvips.Image.new_from_buffer` and `thumbnail_image` for fast, memory-efficient image processing in Python image processing microservices.
