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
    Compresses an uploaded image using pyvips for high performance.
    Changes from async def to def to allow FastAPI to run the CPU-bound
    image processing in a thread pool.
    """
    try:
        # file size validation without reading entire file into memory first
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

        # read uploaded file
        image_bytes = file.file.read()

        # Use thumbnail_buffer for ultra-fast combined loading and resizing.
        # size='down' ensures we only shrink and never upscale, matching previous logic.
        try:
            img = pyvips.Image.thumbnail_buffer(image_bytes, 1600, size='down')
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

        # convert to RGB by flattening alpha channel (required for JPEG)
        if img.hasalpha():
            img = img.flatten()

        # compress image using pyvips
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
        # Re-raise HTTPExceptions to prevent them from being caught by generic Exception
        raise

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )