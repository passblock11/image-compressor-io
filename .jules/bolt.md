## 2025-10-06 - FastAPI CPU-bound image processing & Pillow JPEG draft downscaling
**Learning:**
1. In FastAPI, defining CPU-bound endpoints as `async def` blocks the main asyncio event loop during heavy operations like image decoding/resizing. Switching to synchronous `def` offloads work to Starlette's worker thread pool, maintaining server throughput.
2. Using Pillow's `img.draft()` for JPEG downscaling prior to full load decodes directly at reduced resolution, yielding a ~70% latency reduction (622ms -> 180ms on 6000x4000 images).

**Action:** Always check if CPU-bound endpoints in FastAPI are using `def` instead of `async def`, and enable decoder draft downscaling when downscaling large JPEG images.
