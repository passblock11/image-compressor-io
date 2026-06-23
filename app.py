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
    Compresses an image using pyvips for high performance.
    The endpoint is synchronous to leverage FastAPI's thread pool for CPU-bound work.
    """
    try:
        # Access the underlying file object for synchronous reading
        f = file.file

        # Validate file size without loading everything into memory first
        f.seek(0, io.SEEK_END)
        file_size = f.tell()
        f.seek(0)

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

        image_bytes = f.read()

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    try:
        # Load image metadata to check dimensions
        # new_from_buffer is lazy and very fast
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        MAX_WIDTH = 1600

        # Resize if image is wider than MAX_WIDTH
        if img.width > MAX_WIDTH:
            # Use thumbnail_buffer for 'shrink-on-load' optimization.
            # We set a very large height to ensure the constraint is on width.
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # Handle transparency: convert RGBA/P to RGB by flattening onto a white background
        # This provides better results than just dropping the alpha channel
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Compress and save as JPEG
        # Q: quality (match original 80)
        # optimize_coding: Huffman table optimization (match original optimize=True)
        # interlace: progressive JPEG (match original progressive=True)
        # strip: remove metadata for smaller size
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
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Image processing failed"
        )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
