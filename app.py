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
def compress(file: UploadFile = File(...)):
    # 1. Memory-efficient size validation (Steps 1 & 2)
    # Seek to end of the file to determine size without reading the whole file into memory first
    try:
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

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

    # 2. Read file bytes synchronously
    try:
        image_bytes = file.file.read()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    # 3. Load image with pyvips (Steps 3 & 4)
    try:
        # Load metadata lazily to inspect properties first
        vimg = pyvips.Image.new_from_buffer(image_bytes, "")

        # Check if resize is required (width > 1600)
        # Use shrink-on-load via thumbnail_buffer for maximum efficiency
        MAX_WIDTH = 1600
        if vimg.width > MAX_WIDTH:
            # We set high height constraint to preserve aspect ratio based on width limit
            vimg = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # Ensure image is in sRGB color space
        vimg = vimg.colourspace("srgb")

        # Flatten transparent / alpha channel images on a white background
        if vimg.hasalpha():
            vimg = vimg.flatten(background=[255, 255, 255])

        # Save image to JPEG buffer with high efficiency parameters
        output_bytes = vimg.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            strip=True
        )

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except HTTPException:
        # Re-raise any specific HTTPExceptions
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
