from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    """
    Compresses an image using pyvips for high performance.
    - Synchronous endpoint to avoid blocking the event loop with CPU-bound work.
    - Uses thumbnail_buffer for fast resize-on-load.
    - Efficiently validates file size without full memory load.
    """
    try:
        # Efficient file size validation using seek and tell
        # This avoids reading the file into memory just for size check
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

        # Read the file content for processing
        image_bytes = file.file.read()

        try:
            # Use thumbnail_buffer for ultra-fast resizing during load
            # thumbnail_buffer is significantly faster than decoding the whole image
            # then resizing, as it performs downsampling during the decode process.
            MAX_WIDTH = 1600
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH)

            # Convert to RGB by flattening alpha if present (JPEG doesn't support alpha)
            if img.hasalpha():
                img = img.flatten()

            # Compress to JPEG with optimized parameters
            # Q=80: Good balance of quality/file size
            # optimize_coding=True: Further reduces file size
            # interlace=True: Enables progressive JPEG loading
            output_bytes = img.jpegsave_buffer(
                Q=80,
                optimize_coding=True,
                interlace=True
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

    except HTTPException:
        # Re-raise HTTPExceptions to prevent them from being caught by generic handler
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
