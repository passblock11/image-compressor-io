## 2025-07-29 - [Async Blocking and pyvips Shrink-On-Load Optimizations]
**Learning:** CPU-bound tasks such as image processing/compression should not be run in FastAPI's async def endpoints directly because they block the main event loop, causing severe request serialization. Furthermore, migrating from Pillow to pyvips provides extreme performance improvements. Utilizing 'shrink-on-load' via `thumbnail_buffer` reads only the necessary pixels for target scaling, reducing processing latency by ~40-63%.
**Action:** Always implement CPU-heavy endpoints using synchronous `def` so FastAPI automatically schedules them on its worker thread pool, and prioritize `pyvips` with lazy loading via `new_from_buffer` and `thumbnail_buffer` over Pillow.

## 2025-07-29 - [HTTPException Swallowing Anti-Pattern]
**Learning:** Placing file validation logic that raises FastAPI `HTTPException` inside a general `try...except Exception` block leads to the exception being swallowed and replaced with a generic 500 or 400 error response.
**Action:** Perform file size and empty file validations first before entering the main `try` block, or explicitly capture and re-raise `HTTPException` to guarantee precise client feedback.
