# Bolt Performance Journal

## 2026-03-08 - Pyvips Migration and Sync FastAPI Endpoints for Image Processing

**Learning:** Replacing Pillow with `pyvips` for image compression reduces processing latency by ~50% (e.g. from 185ms down to 93ms on a 3000x2000 image) while lowering memory overhead. Additionally, defining CPU-intensive FastAPI routes as synchronous `def` offloads work to Starlette's worker thread pool, preventing CPU bound operations from blocking asyncio event loops.

**Action:** Prefer `pyvips` over Pillow for high-throughput image manipulation tasks, and always use synchronous `def` handlers for CPU-bound tasks in FastAPI.
