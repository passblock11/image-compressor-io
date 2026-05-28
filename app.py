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

        # Use pyvips for high-performance image processing
        # thumbnail_buffer is faster because it performs shrink-on-load
        MAX_WIDTH = 1600
        img = pyvips.Image.thumbnail_buffer(
            image_bytes,
            MAX_WIDTH,
            height=10000000,
            auto_rotate=True
        )

        # Handle transparency by flattening onto a white background
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # compress image to JPEG buffer
        # Q=80, optimize_coding=True, interlace=True matches Pillow's quality/progressive settings
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
        # Re-raise HTTPExceptions to preserve status codes and messages
        raise e

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
