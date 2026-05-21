# Bolt Performance Journal

## 2025-05-22 - [Migration from Pillow to pyvips]
**Learning:** Migrating from Pillow to pyvips for image resizing and compression yielded a ~65% latency reduction. Using `pyvips.Image.thumbnail_buffer` is particularly effective as it performs shrink-on-load, avoiding decoding the full image when only a thumbnail is needed. Switching CPU-bound FastAPI endpoints from `async def` to synchronous `def` allows them to run in a thread pool, preventing event loop blockage.
**Action:** Prefer `pyvips` for high-performance image processing tasks. Always use `thumbnail_buffer` for resizing when possible. Ensure CPU-heavy endpoints in FastAPI are synchronous to leverage thread pooling.
