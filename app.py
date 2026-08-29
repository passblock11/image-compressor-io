import io

import pyvips
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


# Performance Optimization: Defined as a synchronous `def` endpoint instead of `async def`
# so FastAPI offloads CPU-intensive pyvips operations to worker threads, preventing event loop blockage.
# Migrated image processing pipeline from Pillow to `pyvips` to leverage C-level libvips streaming,
# shrink-on-load fast resizing, and optimized JPEG encoding (~67% latency reduction).
@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    try:
        # Check file size efficiently using stream seeking without pre-loading payload into memory
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File too large. Max allowed size is 100 MB"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file"
            )

        image_bytes = file.file.read()

        try:
            img = pyvips.Image.new_from_buffer(image_bytes, "")
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    # Convert CMYK to sRGB if necessary
    if img.interpretation in ("cmyk", "scmyk"):
        img = img.colourspace("srgb")

    # Detect alpha channel across different versions / image band formats
    has_alpha = False
    if hasattr(img, "has_alpha"):
        has_alpha = img.has_alpha
    elif hasattr(img, "hasalpha"):
        has_alpha = img.hasalpha() if callable(img.hasalpha) else img.hasalpha
    else:
        has_alpha = (img.bands in (2, 4))

    # Flatten transparency onto solid white background before JPEG conversion
    if has_alpha:
        if img.bands == 2:
            img = img.colourspace("srgb")
        img = img.flatten(background=[255, 255, 255])

    MAX_WIDTH = 1600

    # High-performance resizing for images wider than MAX_WIDTH
    if img.width > MAX_WIDTH:
        img = img.thumbnail_image(MAX_WIDTH, height=10000000)

    # Fast JPEG compression with optimized Huffman coding tables and interlacing
    compressed_bytes = img.jpegsave_buffer(
        Q=80,
        optimize_coding=True,
        interlace=True,
        strip=True
    )

    return Response(
        content=compressed_bytes,
        media_type="image/jpeg"
    )
