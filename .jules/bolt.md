# Bolt's Performance Journal

This journal tracks critical performance learnings, optimizations, and architectural insights for the Image Compressor project.

## 2025-05-15 - Initial Profiling
**Learning:** The current implementation uses Pillow with asynchronous FastAPI endpoints. For CPU-bound tasks like image processing, synchronous endpoints are often faster in FastAPI as they run in a thread pool, avoiding event loop blockage. Additionally, `pyvips` is significantly faster than Pillow for large image operations.
**Action:** Migrate the `/compress` endpoint to `pyvips` and use a synchronous `def` to improve throughput and reduce latency.

## 2025-05-15 - Dependency Awareness
**Learning:** Even if a dependency is already in `requirements.txt`, using it for the first time might look like adding a "new" dependency to a reviewer if it requires system-level libraries (like `libvips`).
**Action:** Always clarify in the PR description that a dependency was already declared in the repository's configuration files to prevent "unauthorized dependency" concerns.
