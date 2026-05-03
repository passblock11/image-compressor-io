from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips
import io

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    """
    Compresses an uploaded image using pyvips for high performance.
    The endpoint is synchronous to leverage FastAPI's thread pool for CPU-bound tasks.
    """
    try:
        # Optimized file size validation: seek to end to get size without reading into RAM
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

        # pyvips.Image.thumbnail_buffer is ultra-fast as it performs shrink-on-load.
        # size='down' ensures we only downsize and never upscale.
        # We use a very large height to ensure the constraint is primarily on width.
        try:
            img = pyvips.Image.thumbnail_buffer(
                image_bytes,
                MAX_WIDTH,
                height=10_000_000,
                size='down'
            )
        except pyvips.Error as e:
            error_msg = str(e)
            if "not a known format" in error_msg or "not in a known format" in error_msg:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid image file"
                )
            raise

        # JPEG doesn't support alpha channels, so flatten to RGB if needed
        if img.hasalpha():
            img = img.flatten()

        # Compress to JPEG buffer
        # Q=80: Quality level
        # optimize_coding=True: Optimize Huffman tables (equivalent to Pillow's optimize=True)
        # interlace=True: Create a progressive JPEG (equivalent to Pillow's progressive=True)
        output_buffer = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True
        )

        return Response(
            content=output_buffer,
            media_type="image/jpeg"
        )

    except HTTPException:
        # Re-raise FastAPI HTTPExceptions
        raise
    except Exception:
        # Catch-all for other processing errors
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
