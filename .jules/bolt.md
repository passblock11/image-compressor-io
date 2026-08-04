# Bolt's Performance Journal

This journal tracks critical learnings and performance optimizations for this application.

## 2025-03-04 - [Pillow Image Resizing and Buffer Optimization]
**Learning:** In Pillow, using `Image.BICUBIC` instead of `Image.LANCZOS` provides a significant speed advantage for resizing with negligible visual difference. Additionally, validating file sizes using seek and tell avoids loading large files into memory twice.
**Action:** Replace `Image.LANCZOS` with `Image.BICUBIC` and optimize file size verification and file-like reading.
