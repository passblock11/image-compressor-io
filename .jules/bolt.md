# Bolt's Journal - Critical Learnings Only

## 2025-02-18 - High-performance Image Processing with pyvips

**Learning:** Migrating from Pillow to pyvips dramatically reduces CPU overhead and latency (often by 40% to 60%). Key optimization techniques in pyvips include:
1. Using `thumbnail_buffer` for "shrink-on-load" optimization. This reads and decodes only the pixels required for the target size directly from the source bytes, significantly saving time and memory.
2. Checking image metadata lazily using `new_from_buffer` before executing any expensive resize operations.
3. Avoiding unsupported arguments in `jpegsave_buffer` (like `subsampling_mode`) which can lead to runtime `pyvips.error.Error` exceptions in pyvips version 3.1.1.
4. Using `Q` instead of `quality` to set the JPEG compression quality in `jpegsave_buffer`.
5. Ensuring the core route is synchronous (`def` instead of `async def`) so FastAPI processes CPU-bound operations in its optimized thread pool, preventing event loop blockages.

**Action:** When working on CPU-heavy image manipulation services, migrate from Pillow to pyvips using a synchronous endpoint, check size/properties lazily first, use `thumbnail_buffer` with `height` constraints, and be mindful of environment-specific binding arguments.
