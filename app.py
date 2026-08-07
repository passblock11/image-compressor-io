import io

import pyvips
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    """
    Highly-optimized image compression endpoint using pyvips.
    Runs synchronously to let FastAPI execute CPU-bound tasks in a worker thread pool.
    """
    # 1. Efficiently check the file size without reading it completely into memory
    try:
        file.file.seek(0, io.SEEK_END)
        size = file.file.tell()
        file.file.seek(0)
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Upload failed")

    if size == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File too large. Max allowed size is 100 MB"
        )

    # 2. Read the image bytes
    try:
        image_bytes = file.file.read()
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Upload failed")

    # 3. Open image lazily with pyvips
    try:
        img = pyvips.Image.new_from_buffer(image_bytes, "")
    except pyvips.Error:
        raise HTTPException(status_code=400, detail="Invalid image file")
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Upload failed")

    # 4. Perform image transformations and compression
    try:
        MAX_WIDTH = 1600
        # Check width and resize using thumbnail_image for maximum performance
        if img.width > MAX_WIDTH:
            img = img.thumbnail_image(MAX_WIDTH, height=10000000)

        # Handle transparency: flatten images with alpha channels onto a white background
        has_alpha = img.hasalpha() if callable(img.hasalpha) else img.hasalpha
        if has_alpha:
            img = img.flatten(background=[255, 255, 255])

        # Convert to srgb to ensure consistent RGB output
        img = img.colourspace("srgb")

        # Compress and save to JPEG buffer with optimized parameters
        compressed = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            strip=True,
            interlace=True
        )
    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file or processing error"
        )
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Upload failed")

    return Response(
        content=compressed,
        media_type="image/jpeg"
    )
