# Bolt Journal ⚡

## 2025-06-14 - Performance Boost for Image Compression
**Learning:** Migrating from Pillow to \`pyvips\` and switching from \`async def\` to a synchronous \`def\` endpoint yields a massive (~67%) latency reduction for CPU-bound image processing. Pillow's progressive/optimize flags are significantly slower than \`libvips\` equivalents. Synchronous \`def\` in FastAPI is superior for CPU-heavy tasks as it leverages an external thread pool, preventing event loop starvation.
**Action:** Always prefer \`pyvips\` with 'shrink-on-load' (thumbnail) and synchronous endpoints for high-throughput image processing services.
