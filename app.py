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
    # File size validation without reading entire file into memory first
    # This optimization avoids redundant memory allocation for large files that exceed the limit
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
        # Read the file content for processing
        image_bytes = file.file.read()

        # Use pyvips for high-performance image processing.
        # We first load the image metadata to check if resizing is actually needed.
        # new_from_buffer is lazy and doesn't decode the whole image immediately.
        try:
            img = pyvips.Image.new_from_buffer(image_bytes, "")
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

        MAX_WIDTH = 1600

        # Resize large images using 'shrink-on-load' optimization
        if img.width > MAX_WIDTH:
            # thumbnail_buffer is much faster as it only decodes the pixels needed for the target size.
            # We use a very large height to ensure the constraint is only applied to the width.
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # Handle transparency by flattening onto a white background
        # This maintains visual parity with the original Pillow convert("RGB") behavior.
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Compress and save to JPEG buffer.
        # optimize_coding=True is equivalent to Pillow's optimize=True.
        # interlace=True is equivalent to Pillow's progressive=True.
        # strip=True removes metadata (EXIF, etc.), further reducing file size.
        output_buffer = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            strip=True
        )

        return Response(
            content=output_buffer,
            media_type="image/jpeg"
        )

    except HTTPException:
        # Re-raise HTTPExceptions (like "Invalid image file") so they aren't caught by the general Exception block
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
