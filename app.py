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
    Optimizations:
    - Uses synchronous endpoint to leverage FastAPI's thread pool for CPU-bound work.
    - Uses pyvips.Image.thumbnail_buffer for ultra-fast loading and resizing.
    - Efficiently validates file size without reading full content first.
    """
    try:
        # file size validation using seek/tell to avoid early RAM bloat
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

        # Efficiently load and resize if needed (limit to 1600px box)
        # size='down' ensures we never upscale small images
        img = pyvips.Image.thumbnail_buffer(image_bytes, 1600, size='down')

        # Convert to RGB by flattening alpha channel (required for JPEG)
        if img.hasalpha():
            img = img.flatten()

        # Export to JPEG buffer with optimizations
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True
        )

        return Response(
            content=output_bytes,
            media_type="image/jpeg"
        )

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
    except HTTPException:
        # Re-raise known HTTP exceptions
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
