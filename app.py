from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips
import io

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    """
    Compresses an uploaded image using pyvips for high performance.
    Switched to synchronous def to allow FastAPI to use its thread pool for CPU-bound tasks.
    """
    try:
        # Efficiently validate file size using seek/tell
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

        # Load image lazily to check dimensions
        try:
            img = pyvips.Image.new_from_buffer(image_bytes, "")
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

        if img.width > MAX_WIDTH:
            # Use shrink-on-load for better performance when resizing
            # height=10000000 ensures aspect ratio is preserved based on width
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # Handle alpha channel (transparency) by flattening onto white background
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Ensure we are in sRGB color space (3 bands) for JPEG
        if img.bands != 3:
            img = img.colourspace("srgb")

        # Compress to JPEG buffer with optimization and progressive interlace
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
