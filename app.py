from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips
import os

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    """
    Compresses an image using pyvips for high performance.
    Uses a synchronous endpoint as image processing is CPU-bound,
    allowing FastAPI to run it in a thread pool and avoid blocking the event loop.
    """
    try:
        # Validate file size without loading the entire content into memory first
        file.file.seek(0, os.SEEK_END)
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

        # Read the file content
        image_bytes = file.file.read()

        # Use thumbnail_buffer for ultra-fast resizing during loading.
        # It performs shrink-on-load when possible (e.g., for JPEGs),
        # significantly reducing memory usage and processing time.
        try:
            # Constrain by width while preserving aspect ratio (height set to very large)
            # size='down' ensures we only downscale and never upscale
            img = pyvips.Image.thumbnail_buffer(
                image_bytes,
                MAX_WIDTH,
                height=10000000,
                size='down'
            )
        except pyvips.Error as e:
            err_msg = str(e).lower()
            if "not a known format" in err_msg or "not in a known format" in err_msg:
                raise HTTPException(status_code=400, detail="Invalid image file")
            raise HTTPException(status_code=400, detail="Upload failed")

        # JPEG format doesn't support alpha channel; flatten the image if it has one
        if img.hasalpha():
            img = img.flatten()

        # Save to JPEG buffer with optimized settings
        # Q=80 matches the original quality setting
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True
        )

        return Response(
            content=output_bytes,
            media_type="image/jpeg"
        )

    except HTTPException:
        # Re-raise HTTPExceptions to prevent them from being caught by the generic Exception handler
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
