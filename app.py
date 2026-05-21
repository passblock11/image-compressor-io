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
        # Optimized file size validation without reading entire file into memory first
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

        image_bytes = file.file.read()

        # pyvips.Image.thumbnail_buffer is extremely fast as it performs
        # shrink-on-load for supported formats (like JPEG).
        # We set height to a very large value to ensure we only constrain by width.
        # size='down' ensures we don't upscale small images.
        try:
            img = pyvips.Image.thumbnail_buffer(
                image_bytes,
                MAX_WIDTH,
                height=10000000,
                size='down'
            )
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

        # Handle transparency by flattening onto a white background,
        # matching Pillow's behavior when converting RGBA to RGB.
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # jpegsave_buffer parameters:
        # Q: quality (80)
        # optimize_coding: similar to Pillow's optimize=True
        # interlace: similar to Pillow's progressive=True
        # subsample_mode: 'on' enables 4:2:0 subsampling, matching Pillow's subsampling=2
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            subsample_mode='on'
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
