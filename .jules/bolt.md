# Bolt's Performance Journal

## 2025-05-14 - Initial Optimization Strategy
**Learning:** For CPU-bound tasks like image processing in FastAPI, using synchronous `def` instead of `async def` allows FastAPI to run the handler in a thread pool, preventing the event loop from being blocked. Additionally, stream-based file handling (using `file.file`) and choosing the right resampling filter (BICUBIC over LANCZOS) can significantly reduce memory usage and processing time.
**Action:** Transition the `/compress` endpoint to a synchronous handler and implement stream-based processing.
