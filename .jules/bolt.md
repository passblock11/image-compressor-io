## 2025-05-22 - Performance Gains with pyvips and Sync Endpoints
**Learning:** Migrating from Pillow to pyvips for CPU-bound image processing significantly reduces latency (~57% in this case). Additionally, switching from `async def` to sync `def` in FastAPI allows offloading these CPU-bound tasks to a thread pool, preventing event loop blockage and improving overall concurrency.
**Action:** Always consider pyvips for heavy image processing tasks and use synchronous endpoints for CPU-bound operations in FastAPI.
