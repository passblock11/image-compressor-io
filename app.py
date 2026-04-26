from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips
import os

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    """
    Compresses an image using pyvips.
    Uses 'def' instead of 'async def' to run in a thread pool,
    as image processing is CPU-bound.
    """
    try:
        # validate file size without reading entire file into memory
        file.file.seek(0, os.SEEK_END)
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

        # read image data
        image_bytes = file.file.read()

        # open image using pyvips thumbnail_buffer for efficient loading and resizing
        MAX_WIDTH = 1600

        # We try to load the image. If it's larger than MAX_WIDTH, we let thumbnail_buffer
        # handle the resize during load for maximum performance.
        try:
            # Use thumbnail_buffer to resize while loading
            # size='down' ensures we only downsize
            img = pyvips.Image.thumbnail_buffer(
                image_bytes,
                MAX_WIDTH,
                height=10000,
                size='down'
            )
        except pyvips.Error as e:
            if "not in a known format" in str(e) or "not a known format" in str(e):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid image file"
                )
            raise

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during processing: {e}")
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    # ensure image is in RGB for JPEG saving
    if img.hasalpha():
        img = img.flatten()

    # compress image to JPEG
    # Q=80, optimize_coding=True, interlace=True matches Pillow's quality=80, optimize=True, progressive=True
    output_bytes = img.jpegsave_buffer(
        Q=80,
        optimize_coding=True,
        interlace=True
    )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
