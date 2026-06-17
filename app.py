from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips
import io

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    # Performance Optimization: Switching to sync 'def' allows FastAPI to use a thread pool
    # for CPU-bound image processing, preventing event loop blockage.

    try:
        # Efficient file size validation without reading entire file first
        file.file.seek(0, io.SEEK_END)
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

        # Performance Optimization: pyvips is significantly faster than Pillow for resizing/saving
        # Use new_from_buffer first to check dimensions lazily
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        MAX_WIDTH = 1600
        if img.width > MAX_WIDTH:
            # Use 'shrink-on-load' optimization with thumbnail_buffer
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH)

        # Ensure consistent visual behavior for images with alpha channels
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Compress image to JPEG
        # 'strip=True' removes metadata, similar to Pillow's optimize flag.
        # 'interlace=True' enables progressive JPEG.
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            strip=True
        )

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except HTTPException:
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