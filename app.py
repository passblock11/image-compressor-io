from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips
import logging

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
    Uses synchronous endpoint to leverage FastAPI's thread pool for CPU-bound tasks.
    """
    try:
        # Validate file size without loading entire file into memory first
        file.file.seek(0, 2)
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

        # pyvips.Image.thumbnail_buffer is extremely fast as it performs
        # shrinking during the load process.
        # size='down' ensures we only shrink, never upscale.
        try:
            img = pyvips.Image.thumbnail_buffer(
                image_bytes,
                MAX_WIDTH,
                size='down'
            )
        except pyvips.Error as e:
            if "not in a known format" in str(e) or "not a known format" in str(e):
                raise HTTPException(status_code=400, detail="Invalid image file")
            raise

        # JPEG does not support alpha channel, so flatten if necessary
        if img.hasalpha():
            img = img.flatten()

        # Compress to JPEG buffer with optimized settings
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
        # Re-raise FastAPI HTTPExceptions to avoid them being caught by generic handler
        raise
    except Exception as e:
        logging.error(f"Compression failed: {e}")
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
