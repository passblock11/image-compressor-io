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
    FastAPI handles sync 'def' in a thread pool, ideal for CPU-bound image processing.
    """

    try:
        # validate file size without reading into memory
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max allowed size is {MAX_FILE_SIZE // (1024 * 1024)} MB"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file"
            )

        # Read the file data for pyvips
        image_data = file.file.read()

        # Use pyvips.Image.thumbnail_buffer for fast resizing during load
        # This is much faster as it only decodes the required pixels
        MAX_WIDTH = 1600
        img = pyvips.Image.thumbnail_buffer(image_data, MAX_WIDTH)

    except HTTPException:
        # Re-raise HTTPExceptions to avoid them being caught by the generic Exception block
        raise

    except pyvips.Error as e:
        if "not in a known format" in str(e) or "not a known format" in str(e):
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    # Convert to RGB (flatten alpha) if necessary before JPEG save
    if img.hasalpha():
        img = img.flatten()

    # Compress image to JPEG buffer
    # subsampling_mode=0 is 4:4:4, 1 is 4:2:2, 2 is 4:2:0 (default)
    compressed_data = img.jpegsave_buffer(
        Q=80,
        optimize_coding=True,
        interlace=True
    )

    return Response(
        content=compressed_data,
        media_type="image/jpeg"
    )