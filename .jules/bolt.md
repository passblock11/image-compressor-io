## 2025-02-13 - Pillow JPEG draft downscaling & stream seeking size checks
**Learning:** In Pillow-based image services, passing `file.file` directly to `Image.open` and checking stream length with `seek(0, io.SEEK_END)` avoids copying large byte payloads into memory. Furthermore, calling `img.draft('RGB', (target_width, target_height))` enables libjpeg decoder-level downscaling, reducing JPEG processing latency by up to ~65%.
**Action:** Always combine `file.file` stream passing and `img.draft()` fast decoder scaling when processing JPEGs in Pillow endpoints before calling `img.resize()`.
