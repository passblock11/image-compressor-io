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
        # Use seek/tell to check file size without reading everything into memory first
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

        # Read the file content
        image_bytes = file.file.read()

        MAX_WIDTH = 1600

        # Use thumbnail_buffer for fast loading and resizing.
        # We set height to a very large value to only constrain the width,
        # matching the previous Pillow implementation's logic.
        # size='down' ensures we only downscale and never upscale.
        try:
            img = pyvips.Image.thumbnail_buffer(
                image_bytes,
                MAX_WIDTH,
                height=10000000,
                size='down'
            )
        except pyvips.Error as e:
            err_msg = str(e)
            if "not a known format" in err_msg or "not in a known format" in err_msg:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid image file"
                )
            raise HTTPException(
                status_code=400,
                detail="Upload failed"
            )

        # Flatten alpha channel if present before saving as JPEG
        if img.hasalpha():
            img = img.flatten()

        # Save to JPEG buffer with high-performance settings
        # Q=80, optimize_coding=True, interlace=True (progressive)
        compressed_data = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True
        )

        return Response(
            content=compressed_data,
            media_type="image/jpeg"
        )

    except HTTPException:
        # Re-raise HTTPExceptions (like validation errors)
        raise
    except Exception:
        # Catch-all for any other errors
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
