from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    """
    Compresses an image using pyvips for high performance.
    Uses synchronous endpoint to leverage FastAPI's thread pool for CPU-bound tasks.
    """
    try:
        # Zero-copy file size validation
        file.file.seek(0, 2)
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

        # Read file content for pyvips
        image_bytes = file.file.read()

        # pyvips.Image.thumbnail_buffer is extremely fast as it performs
        # shrinking during the load process.
        MAX_WIDTH = 1600

        # Load and potentially resize image
        img = pyvips.Image.thumbnail_buffer(
            image_bytes,
            MAX_WIDTH,
            height=1000000, # Large number to effectively ignore height constraint and maintain aspect ratio
            no_rotate=False
        )

    except pyvips.Error as e:
        error_msg = str(e)
        if "not in a known format" in error_msg or "not a known format" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    # Flatten alpha channel if present (JPEG doesn't support it)
    if img.hasalpha():
        img = img.flatten()

    # Save to JPEG buffer with optimizations
    # pyvips jpegsave_buffer parameters:
    # Q: quality (default 75, we use 80)
    # optimize_coding: use Huffman table optimization
    # interlace: create a progressive JPEG
    output_bytes = img.jpegsave_buffer(
        Q=80,
        optimize_coding=True,
        interlace=True
    )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
