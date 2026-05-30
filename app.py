from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips
import logging

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600

@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    try:
        # File size validation without loading everything into memory first
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

        # Load and resize in one step if possible using thumbnail_buffer
        # We use a very large height to only constrain by width
        img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # convert unsupported modes / handle transparency
        # pyvips.Image.thumbnail_buffer handles many formats,
        # but we need to ensure it's RGB for JPEG
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # compress image to JPEG buffer
        # interlace=True for progressive JPEG
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
    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except Exception as e:
        logging.error(f"Compression failed: {e}")
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
