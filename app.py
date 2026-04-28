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
    """
    Synchronous endpoint for CPU-bound image processing.
    FastAPI will run this in a thread pool.
    """
    try:
        # Check file size without reading full content into memory first
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

        image_bytes = file.file.read()

        MAX_WIDTH = 1600

        # Use pyvips for fast thumbnailing (shrink-on-load)
        # thumbnail_buffer is significantly faster than decoding then resizing
        img = pyvips.Image.thumbnail_buffer(
            image_bytes,
            MAX_WIDTH,
            size='down'
        )

        # Ensure we have RGB for JPEG (flatten alpha if present)
        if img.hasalpha():
            img = img.flatten()

        # Save to JPEG buffer with optimized settings
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True
        )

        return Response(
            content=output_bytes,
            media_type="image/jpeg"
        )

    except HTTPException:
        raise
    except pyvips.Error as e:
        # Handle invalid image formats
        err_msg = str(e)
        if "not in a known format" in err_msg or "not a known format" in err_msg:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )
        raise HTTPException(
            status_code=400,
            detail=f"Image processing failed: {err_msg}"
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
