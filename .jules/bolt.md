## 2026-06-06 - [Optimizing image compression with pyvips]
**Learning:** Migrating from Pillow to pyvips for image compression and resizing, combined with switching to a synchronous FastAPI endpoint for CPU-bound tasks, significantly reduces latency (approx. 65% in this case). Synchronous endpoints in FastAPI prevent blocking the event loop by running in a thread pool.
**Action:** Always prefer pyvips for heavy image processing and use synchronous endpoints for CPU-bound tasks in FastAPI to maximize throughput.
