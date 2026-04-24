from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips

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
    Optimized to use minimal memory and fast resizing.
    """
    try:
        # Optimized file size validation: seek to end to get size without reading into RAM
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

        # Read the file content
        image_bytes = file.file.read()

        # Use thumbnail_buffer for ultra-fast resizing during load.
        # This avoids decoding the full image if it needs to be downscaled.
        img = pyvips.Image.thumbnail_buffer(
            image_bytes,
            MAX_WIDTH,
            height=10000000,  # Effectively ignore height constraint
            size='down'
        )

    except HTTPException:
        # Explicitly re-raise HTTPExceptions to prevent them from being caught by generic except
        raise
    except pyvips.Error as e:
        error_msg = str(e).lower()
        if "not a known format" in error_msg or "not in a known format" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    # Flatten images with alpha channel for JPEG compatibility
    if img.hasalpha():
        img = img.flatten()

    # Compress image using jpegsave_buffer with optimized settings
    # Q=80, optimize_coding=True, and interlace=True (progressive)
    output_bytes = img.jpegsave_buffer(
        Q=80,
        optimize_coding=True,
        interlace=True
    )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
