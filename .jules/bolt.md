## 2026-03-30 - Migrating image processing from Pillow to pyvips
**Learning:** pyvips uses streaming and lazy evaluation ('shrink-on-load'), which processes image compression significantly faster than Pillow (up to ~3x speedup). In FastAPI endpoints, making CPU-bound processing functions synchronous (`def` instead of `async def`) offloads execution to Starlette's thread pool, avoiding blocking the main event loop.
**Action:** Use pyvips for fast image resizing/compression and standard `def` for CPU-bound FastAPI routes.
