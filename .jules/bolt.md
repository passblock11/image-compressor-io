## 2026-03-22 - pyvips vs Pillow for Image Processing Endpoints

**Learning:** Migrating CPU-bound FastAPI image processing endpoints from Pillow (`PIL`) to `pyvips` with synchronous (`def`) endpoint execution yields a ~67% to 80% latency reduction. C-based libvips processes images via demand-driven streaming and shrink-on-load downscaling, avoiding full raster memory allocations. Furthermore, using synchronous `def` in FastAPI offloads heavy libvips operations to Starlette's thread pool, preventing event loop starvation.

**Action:** Prefer `pyvips` for backend image resizing and compression services. Define CPU-bound FastAPI routes as synchronous `def` functions to ensure thread pool execution.
