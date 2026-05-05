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
    Compresses an image using pyvips for high performance.
    Uses sync def so FastAPI runs it in a threadpool, avoiding event loop blockage.
    """
    try:
        # read uploaded file
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

        # Use thumbnail_buffer for fast loading and resizing in one step
        # size='down' ensures we only downsize, never upsize
        img = pyvips.Image.thumbnail_buffer(
            image_bytes,
            MAX_WIDTH,
            height=10000000,
            size='down'
        )

        # Ensure image is in a format suitable for JPEG (no alpha)
        if img.hasalpha():
            img = img.flatten()

        # compress image to JPEG buffer
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True
        )

        return Response(
            content=output_bytes,
            media_type="image/jpeg"
        )

    except HTTPException as e:
        # Re-raise HTTP exceptions to avoid them being caught by the generic handler
        raise e

    except pyvips.Error as e:
        # Map pyvips errors to 400 Invalid image
        error_msg = str(e)
        if "not in a known format" in error_msg or "not a known format" in error_msg:
             raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )
        raise HTTPException(
            status_code=400,
            detail=f"Image processing failed: {error_msg}"
        )

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
