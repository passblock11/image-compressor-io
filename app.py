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
    """
    try:
        # Validate file size without reading the whole file into RAM
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max allowed size is {MAX_FILE_SIZE // (1024 * 1024)} MB"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file"
            )

        # Use synchronous def so FastAPI runs this in a thread pool,
        # preventing the event loop from being blocked by image processing.
        image_bytes = file.file.read()

        # Efficiently resize using shrink-on-load
        MAX_WIDTH = 1600
        # thumbnail_buffer is significantly faster than opening then resizing
        img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH)

        # Ensure image is RGB (flatten alpha channel if present)
        if img.hasalpha():
            img = img.flatten()

        # Compress to JPEG buffer with optimized settings
        output_buffer = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True
        )

        return Response(
            content=output_buffer,
            media_type="image/jpeg"
        )

    except HTTPException as e:
        # Re-raise HTTP exceptions to avoid being caught by the generic block
        raise e
    except Exception as e:
        detail = str(e)
        # Map pyvips errors to user-friendly messages
        if "not a known format" in detail.lower():
            raise HTTPException(status_code=400, detail="Invalid image file")

        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )