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
    """
    Synchronous endpoint for CPU-bound image processing.
    FastAPI will run this in an external thread pool.
    """
    try:
        # Check file size without reading everything into memory first
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

        # Read file content
        image_bytes = file.file.read()

        # Try opening image header to check dimensions
        try:
            img = pyvips.Image.new_from_buffer(image_bytes, "")
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

        MAX_WIDTH = 1600

        # Resize if necessary using efficient shrink-on-load
        if img.width > MAX_WIDTH:
            # thumbnail_buffer is highly optimized for this
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH)

        # Handle alpha channel (PNG/RGBA) by flattening onto a white background
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Compress image to JPEG
        # optimize_coding=True matches Pillow's optimize=True
        # interlace=True matches Pillow's progressive=True
        # strip=True removes metadata for further size reduction
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            strip=True
        )

        return Response(
            content=output_bytes,
            media_type="image/jpeg"
        )

    except HTTPException:
        raise
    except Exception as e:
        # In a real app, we'd log 'e'
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
