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
    Compresses an image using pyvips for high performance.
    Uses synchronous 'def' as image processing is CPU-bound.
    """
    try:
        # Read uploaded file synchronously to avoid event loop overhead
        image_bytes = file.file.read()

        # File size validation
        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file"
            )

        if len(image_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File too large. Max allowed size is 100 MB"
            )

        # Use thumbnail_buffer for ultra-fast resizing during load.
        # This is significantly faster than loading the full image and then resizing.
        # size='down' ensures we only downscale, never upscale.
        # A very large height allows us to constrain primarily by width while preserving aspect ratio.
        try:
            img = pyvips.Image.thumbnail_buffer(
                image_bytes,
                MAX_WIDTH,
                height=10000000,
                size='down'
            )
        except pyvips.Error as e:
            err_str = str(e).lower()
            # Handle different variations of "not a known format" from libvips
            if any(msg in err_str for msg in ["not a known format", "unrecognised image format", "not in a known format"]):
                raise HTTPException(status_code=400, detail="Invalid image file")
            raise

        # JPEG doesn't support alpha channels, so flatten if needed
        if img.hasalpha():
            img = img.flatten()

        # Compress image to JPEG buffer
        # optimize_coding=True and interlace=True provide better compression/loading
        output_buffer = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True
        )

        return Response(
            content=output_buffer,
            media_type="image/jpeg"
        )

    except HTTPException:
        # Re-raise FastAPI HTTPExceptions (like validation errors)
        raise
    except Exception:
        # Map all other errors to 'Upload failed' to match original behavior
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
