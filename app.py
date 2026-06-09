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
    Compresses an uploaded image using pyvips for high performance.
    Handles resizing, alpha channel flattening, and JPEG optimization.
    """
    try:
        # Efficiently get file size without reading full content into memory first
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

        # Read file content for processing
        image_bytes = file.file.read()

        # Try opening image to validate and get metadata
        # pyvips.Image.new_from_buffer is lazy
        img = pyvips.Image.new_from_buffer(image_bytes, "")

    except HTTPException:
        raise
    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    # Handle alpha channels (PNG/RGBA) by flattening onto a white background
    if img.hasalpha():
        img = img.flatten(background=[255, 255, 255])

    MAX_WIDTH = 1600

    # Resize large images using thumbnail_buffer for shrink-on-load optimization
    if img.width > MAX_WIDTH:
        img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH)

    # Compress and save as progressive JPEG
    output_bytes = img.jpegsave_buffer(
        Q=80,
        optimize_coding=True,
        interlace=True
    )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )