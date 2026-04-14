## 2025-04-14 - Image Processing Pipeline Optimization
**Learning:** Significant performance gains can be achieved in Python image APIs by avoiding redundant memory copies. Replacing `await file.read()` with stream-based `file.file` usage and `output.getvalue()` prevents multiple allocations of large byte buffers. Additionally, deferring color mode conversion (`RGBA` -> `RGB`) until after a resize operation reduces the workload by processing fewer pixels.
**Action:** Always prefer stream-based file handling for uploads/downloads and defer pixel-heavy transformations until after resizing.
