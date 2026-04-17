## 2025-05-15 - FastAPI CPU-bound Performance & Stream Handling
**Learning:** For CPU-bound tasks like image processing, using synchronous 'def' endpoints in FastAPI is faster than 'async def' because it avoids blocking the event loop and leverages a thread pool. Additionally, loading files via 'file.file' stream instead of 'await file.read()' prevents redundant memory allocation.
**Action:** Default to sync endpoints for image processing and use stream-based file handling to minimize memory footprint.
