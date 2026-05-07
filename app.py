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
    Switched to synchronous endpoint to leverage FastAPI's thread pool for CPU-bound tasks.
    """
    try:
        # read uploaded file content
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

        MAX_WIDTH = 1600

        try:
            # Use pyvips.Image.thumbnail_buffer for ultra-fast resizing during loading.
            # size='down' ensures we only downscale, never upscale.
            # height=10000000 allows aspect-ratio-preserving resize based on width.
            img = pyvips.Image.thumbnail_buffer(
                image_bytes,
                MAX_WIDTH,
                height=10000000,
                size='down'
            )
        except pyvips.Error as e:
            err_msg = str(e).lower()
            if "not a known format" in err_msg or "not in a known format" in err_msg:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid image file"
                )
            raise

        # If image has alpha channel (RGBA, LA, etc.), flatten it onto a background for JPEG compatibility.
        if img.hasalpha():
            img = img.flatten()

        # compress image to JPEG format
        # quality=80, optimize_coding=True, interlace=True for progressive JPEG
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

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
