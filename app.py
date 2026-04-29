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

        # Use thumbnail_buffer for fast loading and resizing
        # size='down' ensures we only downsize, never upscale
        # pyvips is significantly faster than Pillow for large images
        img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, size='down')

    except pyvips.Error as e:
        error_msg = str(e)
        if "not a known format" in error_msg.lower() or "not in a known format" in error_msg.lower():
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

    # Handle alpha channel for JPEG compatibility
    if img.hasalpha():
        img = img.flatten()

    # compress image to JPEG buffer
    # Q=80, optimize_coding=True (optimize), interlace=True (progressive)
    output_bytes = img.jpegsave_buffer(
        Q=80,
        optimize_coding=True,
        interlace=True
    )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
