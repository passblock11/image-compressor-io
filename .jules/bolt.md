## 2025-05-15 - FastAPI Performance Pattern for CPU-bound tasks
**Learning:** Using synchronous `def` instead of `async def` for CPU-bound tasks (like image processing) in FastAPI allows the framework to run them in a separate thread pool, preventing the event loop from being blocked and improving overall throughput.
**Action:** Always prefer `def` endpoints for heavy computation tasks in FastAPI.

## 2025-05-15 - High-performance image processing with pyvips
**Learning:** `pyvips` is significantly faster (~45% in this case) than Pillow for resizing and JPEG compression because it uses a demand-driven, streamed image processing model and can perform "shrink-on-load".
**Action:** Use `pyvips` for high-throughput image processing services when system dependencies allow.
