from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import io
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
    The endpoint is synchronous (def) to allow FastAPI to run it in a thread pool,
    preventing the event loop from being blocked by CPU-bound image processing.
    """
    try:
        # file size validation
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

        # pyvips.Image.new_from_buffer is lazy and only reads metadata
        try:
            img = pyvips.Image.new_from_buffer(image_bytes, "")
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

        MAX_WIDTH = 1600

        # resize large images if width exceeds MAX_WIDTH
        if img.width > MAX_WIDTH:
            # pyvips.Image.thumbnail_buffer performs shrink-on-load for high performance.
            # We use a very large height to ensure the width is the primary constraint.
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # Handle images with alpha channels (like PNG/RGBA) by flattening onto a white background
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Compress image to JPEG buffer
        # Q=80: match original quality
        # optimize_coding=True: match optimize=True (Huffman optimization)
        # interlace=True: match progressive=True (Progressive JPEG)
        # strip=True: remove metadata (EXIF, ICC profiles) to reduce size
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
        raise
    except Exception:
        # General fallback for unexpected errors
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
