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
async def compress(file: UploadFile = File(...)):  # noqa: B008

    try:
        # Check size without loading the whole file into memory first
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

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

        # Read uploaded file
        image_bytes = await file.read()

        # Try loading image lazily with pyvips to check metadata / validate format
        try:
            img = pyvips.Image.new_from_buffer(image_bytes, "")
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

        width = img.width

        MAX_WIDTH = 1600

        # Use shrink-on-load (thumbnail_buffer) if image width exceeds max width
        if width > MAX_WIDTH:
            img = pyvips.Image.thumbnail_buffer(
                image_bytes,
                MAX_WIDTH,
                height=10000000,
                size=pyvips.enums.Size.DOWN
            )

        # Ensure consistent sRGB color profile
        img = img.colourspace("srgb")

        # Handle transparency/alpha channels - flatten onto a white background
        # pyvips hasalpha() returns 1 if an alpha channel is present, or 0 if absent
        has_alpha = img.hasalpha() if callable(img.hasalpha) else img.hasalpha
        if has_alpha:
            img = img.flatten(background=[255, 255, 255])

        # Save buffer as progressive JPEG with optimization and stripped metadata
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            strip=True
        )

    except HTTPException:
        # Re-raise HTTPExceptions to avoid swallowing specific status codes
        raise

    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
