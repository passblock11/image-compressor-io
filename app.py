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
    Uses synchronous def to leverage FastAPI's thread pool for CPU-bound tasks.
    """
    try:
        # Efficient file size validation: seek to end to get size without reading into RAM
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

        # pyvips.Image.thumbnail_buffer is ultra-fast as it performs resizing during file loading.
        # size='down' ensures we only shrink images, never upscale.
        # A very large height allows constraining only by width while preserving aspect ratio.
        img = pyvips.Image.thumbnail_buffer(
            image_bytes,
            MAX_WIDTH,
            height=10_000_000,
            size='down'
        )

        # JPEG does not support alpha channels; flatten if present
        if img.hasalpha():
            img = img.flatten()

        # Compress to JPEG using optimized settings
        output_buffer = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True
        )

        return Response(
            content=output_buffer,
            media_type="image/jpeg"
        )

    except pyvips.Error as e:
        error_msg = str(e)
        # Map pyvips format errors to 400 Invalid image file
        if "not in a known format" in error_msg or "not a known format" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
    except HTTPException:
        # Re-raise FastAPI HTTPExceptions (like file size or empty file)
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
