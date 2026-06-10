import io
import pyvips
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    """
    Compresses an uploaded image using pyvips for high performance.
    Uses sync 'def' to delegate CPU-bound work to a thread pool.
    """
    try:
        # Efficiently check file size before reading into memory
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

        # Read uploaded file
        image_bytes = file.file.read()

        try:
            # new_from_buffer is lazy and fast (only reads header)
            img = pyvips.Image.new_from_buffer(image_bytes, "")
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

        MAX_WIDTH = 1600

        # Resize large images using shrink-on-load for better performance
        if img.width > MAX_WIDTH:
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH)

        # Convert to RGB (flatten transparency if present)
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Ensure we are in a compatible color space for JPEG
        if img.interpretation == 'cmyk':
            img = img.colourspace('srgb')

        # Compress image to JPEG
        # Q=80 matches original quality
        # optimize_coding=True matches optimize=True
        # interlace=True matches progressive=True
        # strip=True removes metadata (matches common 'optimize' behavior)
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            strip=True
        )

        return Response(
            content=output_bytes,
            media_type="image/jpeg"
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )