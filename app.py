import io
import pyvips
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    # Efficient file size validation without reading entire file into memory first
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

    try:
        image_bytes = file.file.read()

        # Load image header to check dimensions
        # This is fast as it doesn't decode the whole image
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        MAX_WIDTH = 1600

        # Performance optimization: use shrink-on-load via thumbnail_buffer
        if img.width > MAX_WIDTH:
            # thumbnail_buffer is much faster than loading then resizing
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH)

        # Handle transparency: flatten RGBA to RGB with white background
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Compress to JPEG
        # optimize_coding=True is equivalent to Pillow's optimize=True
        # interlace=True is equivalent to Pillow's progressive=True
        # strip=True removes metadata (EXIF, etc.)
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

    except pyvips.error.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except HTTPException:
        # Re-raise HTTPExceptions (like Empty file or File too large)
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
