## 2026-05-23 - Baseline Benchmark
**Initial Performance:** ~0.30s for 3000x3000px JPEG images using Pillow and async endpoint.
**Optimization Goal:** Migrate to pyvips and sync endpoint to reduce latency.
## 2026-05-23 - Pillow to pyvips Migration
**Learning:** Migrating from Pillow to pyvips and switching the FastAPI endpoint to synchronous 'def' achieved a ~62% latency reduction (0.303s -> 0.114s) for 3000x3000px images.
**Action:** Use pyvips for CPU-bound image processing and sync endpoints in FastAPI to delegate work to thread pools, preventing event loop blockage.
