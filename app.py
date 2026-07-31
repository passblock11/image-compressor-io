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
    # 1. Early validation of file size and empty status (memory-efficient check)
    try:
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file"
        )

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File too large. Max allowed size is 100 MB"
        )

    try:
        image_bytes = file.file.read()
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    try:
        # 2. Lazily check image metadata to avoid expensive operations on smaller images
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        MAX_WIDTH = 1600
        if img.width > MAX_WIDTH:
            # 3. Use shrink-on-load thumbnail optimization for maximum efficiency
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # 4. Handle transparency safely by flattening the alpha channel with a white background
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # 5. Convert to standard sRGB color space
        img = img.colourspace("srgb")

        # 6. Compress and output high-quality, interlaced, stripped JPEG bytes
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            strip=True
        )
    except pyvips.error.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
