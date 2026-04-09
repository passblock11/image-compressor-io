## 2025-04-09 - Efficient Image Handling with Streams
**Learning:** Transitioning from `await file.read()` (bytes-in-memory) to streaming directly from `file.file` with PIL significantly reduces memory overhead. Performance is also improved by using `BICUBIC` resampling and `getvalue()` for BytesIO responses.
**Action:** Always prefer stream-based processing for large file uploads to maintain low memory footprints and avoid unnecessary RAM allocation.
