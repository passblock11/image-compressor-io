## 2026-03-31 - Pillow Stream Operations and Sync Endpoints in FastAPI
**Learning:** Direct stream processing (`file.file`) and `Image.BICUBIC` resampling significantly reduce image compression latency while lowering memory footprint. Offloading CPU-bound tasks by defining sync `def` FastAPI endpoints prevents event-loop blocking.
**Action:** Use `file.file.seek` for size validation, pass `file.file` directly to `Image.open`, use `Image.BICUBIC` for downscaling, and use synchronous endpoints for CPU-intensive image workloads.
