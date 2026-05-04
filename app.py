from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    """
    Compresses an image using pyvips for high performance.
    Uses synchronous endpoint to allow FastAPI to manage the CPU-bound task in a thread pool.
    """
    try:
        # read uploaded file synchronously
        image_bytes = file.file.read()

        # file size validation
        if len(image_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File too large. Max allowed size is 100 MB"
            )

        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file"
            )

        # Use thumbnail_buffer for ultra-fast resizing on load.
        # height=10000000 ensures it's constrained only by width while preserving aspect ratio.
        # size='down' ensures we never upscale.
        img = pyvips.Image.thumbnail_buffer(
            image_bytes,
            MAX_WIDTH,
            height=10000000,
            size='down'
        )

        # Ensure RGB by flattening alpha channel if present
        if img.hasalpha():
            img = img.flatten()

        # Compress to JPEG buffer
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
        raise
    except pyvips.Error as e:
        # Check if it's an identification error
        err_msg = str(e)
        if "not in a known format" in err_msg or "not a known format" in err_msg:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )
        raise HTTPException(
            status_code=400,
            detail=f"Processing failed: {err_msg}"
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
