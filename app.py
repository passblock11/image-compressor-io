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
    Synchronous endpoint for CPU-bound image compression.
    FastAPI will run this in a thread pool, preventing the event loop from blocking.
    """
    # File size validation using stream pointers (efficient for large files)
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
        # Read the file content synchronously
        image_bytes = file.file.read()

        try:
            # Use pyvips for high-performance image processing.
            # new_from_buffer is lazy and only reads enough to get metadata.
            img = pyvips.Image.new_from_buffer(image_bytes, "")
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

        MAX_WIDTH = 1600

        # High-performance resizing using thumbnail_buffer (shrink-on-load)
        if img.width > MAX_WIDTH:
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH)

        # Ensure consistent behavior for images with transparency (e.g., PNG)
        # Flattening onto a white background matches Pillow's RGBA -> RGB conversion.
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Compress image to JPEG.
        # interlace=True generates progressive JPEGs.
        # optimize_coding=True performs Huffman table optimization.
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True
        )

    except HTTPException:
        # Re-raise HTTPExceptions to preserve status codes and details.
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
