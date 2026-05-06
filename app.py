from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips
import logging

# Configure logging to help diagnose issues in production
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    Processes images synchronously in a thread pool to avoid blocking the event loop.
    """
    try:
        # Optimized file size validation without reading entire file into memory.
        # This protects against memory exhaustion from extremely large uploads.
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max allowed size is {MAX_FILE_SIZE // (1024*1024)} MB"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file"
            )

        # Read file content for processing.
        # UploadFile.file is a spooled temp file, which is efficient.
        image_bytes = file.file.read()

        # Use pyvips for high-performance image processing.
        # thumbnail_buffer is significantly faster than standard loading + resizing
        # as it employs "shrink-on-load" optimizations.
        try:
            img = pyvips.Image.thumbnail_buffer(
                image_bytes,
                MAX_WIDTH,
                height=10_000_000,
                size='down'
            )
        except pyvips.Error as e:
            error_msg = str(e)
            if "not in a known format" in error_msg or "not a known format" in error_msg:
                raise HTTPException(status_code=400, detail="Invalid image file")
            logger.error(f"Pyvips processing error: {error_msg}")
            raise HTTPException(status_code=500, detail="Error processing image")

        # Handle transparency: JPEG doesn't support alpha channels.
        # Flattening onto a default (black) background.
        if img.hasalpha():
            img = img.flatten()

        # Compress using pyvips jpegsave_buffer.
        # Using optimize_coding=True and interlace=True for better web performance.
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
        # Explicitly re-raise HTTPExceptions (like 413 or 400)
        raise
    except Exception as e:
        # Log unexpected errors but don't leak details to the client
        logger.exception(f"Unexpected error during compression: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during processing"
        )
