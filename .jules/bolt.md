## 2026-08-29 - Fast image compression using pyvips and sync endpoints in FastAPI

**Learning:** Migrating CPU-bound image compression from Pillow to `pyvips` alongside converting the endpoint from `async def` to synchronous `def` drastically reduces processing latency (by ~67%). Using `pyvips` avoids in-memory decoding of unused pixels via C-level shrink-on-load streaming, and synchronous `def` offloads CPU work to Starlette's thread pool to avoid blocking FastAPI's main event loop.

**Action:** For CPU-bound image or media processing in FastAPI, use native C libraries (`pyvips`) and define endpoints as synchronous `def` functions. Always include a `.gitignore` to prevent tracking `__pycache__` artifacts.
