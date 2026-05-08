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
    Compresses an image to JPEG format and resizes it if it exceeds MAX_WIDTH.
    Uses pyvips for high-performance image processing.
    """
    try:
        # Get file size without reading everything into memory yet
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        # file size validation
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

        # Use thumbnail_buffer for fast resizing during load
        # size='down' ensures we only downsize, never upscale
        # Providing a massive height ensures the constraint is primarily on width
        try:
            img = pyvips.Image.thumbnail_buffer(
                image_bytes,
                MAX_WIDTH,
                height=10000000,
                size='down'
            )
        except pyvips.Error as e:
            err_msg = str(e).lower()
            if "not a known format" in err_msg or "not in a known format" in err_msg:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid image file"
                )
            raise HTTPException(
                status_code=400,
                detail="Upload failed"
            )

        # Flatten if it has alpha channel (JPEG doesn't support alpha)
        if img.hasalpha():
            img = img.flatten()

        # Compress image to JPEG buffer
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
        # Re-raise HTTPExceptions so they aren't caught by the general block
        raise
    except Exception as e:
        logging.error(f"Unexpected error during compression: {e}")
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
