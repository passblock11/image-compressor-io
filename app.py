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
    Compresses an image using pyvips.
    Optimized for performance by:
    1. Using synchronous def to offload CPU-bound work to FastAPI's thread pool.
    2. Using pyvips for faster image processing compared to Pillow.
    3. Using thumbnail_buffer for efficient resizing during load.
    """
    try:
        # read uploaded file
        image_bytes = file.file.read()

        # file size validation
        if len(image_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File too large. Max allowed size is 100 MB"
            )

        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file"
            )

        # load image with pyvips
        # use thumbnail_buffer to resize during load if it's too wide
        try:
            # We first need to know the width to decide if we use thumbnail_buffer
            # new_from_buffer is lazy, so it's cheap to just get the header
            img = pyvips.Image.new_from_buffer(image_bytes, "")

            if img.get("width") > MAX_WIDTH:
                img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH)
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

        # Handle transparency: flatten to white background
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # compress image to JPEG in memory
        # interlace=True corresponds to progressive=True in Pillow
        output_buffer = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            subsample_mode='on'
        )

        return Response(
            content=output_buffer,
            media_type="image/jpeg"
        )

    except HTTPException:
        # Re-raise HTTPExceptions so they aren't caught by the general Exception block
        raise

    except Exception:
        # Log error if needed: print(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
